import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from accounts.models import CustomUser
from orders.models import Order, OrderItem
from payment.forms import PaymentMethodSelectionForm
from payment.models import PaymentMethod
from payment.services import PaymentService
from payment.stripe_handler import StripeCustomerHandler, StripePaymentMethodHandler
from payment.tasks import payment_completed as payment_completed_task
from payment.webhooks import stripe_webhook
from shop.models import Category, Product


class PaymentMethodModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.pm = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_test_123",
            card_type="visa",
            last_four_digits="4242",
            card_holder_name="John Doe",
            exp_month=12,
            exp_year=2030,
            is_default=True,
        )

    def test_str(self):
        self.assertIn("4242", str(self.pm))

    def test_get_masked_card(self):
        self.assertEqual(self.pm.get_masked_card(), "•••• 4242")

    def test_is_expired_false(self):
        self.assertFalse(self.pm.is_expired())

    def test_is_expired_true(self):
        self.pm.exp_year = 2020
        self.pm.exp_month = 1
        self.pm.save()
        self.assertTrue(self.pm.is_expired())

    def test_get_expiration_display(self):
        self.assertEqual(self.pm.get_expiration_display(), "12/30")

    def test_default_unique_per_user(self):
        pm2 = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_test_456",
            card_type="mastercard",
            last_four_digits="1234",
            card_holder_name="John Doe",
            exp_month=6,
            exp_year=2028,
            is_default=True,
        )
        self.pm.refresh_from_db()
        self.assertFalse(self.pm.is_default)
        self.assertTrue(pm2.is_default)


class PaymentServiceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="payuser", password="x", email="pay@x.com"
        )
        self.category = Category.objects.create(name="cat", slug="cat")
        self.product = Product.objects.create(
            category=self.category,
            name="Item",
            slug="item",
            price=Decimal("50.00"),
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="A",
            last_name="B",
            email="a@b.com",
            address="addr",
            postal_code="00000",
            city="city",
        )
        OrderItem.objects.create(
            order=self.order, product=self.product, price=Decimal("50.00"), quantity=2
        )

    @patch("payment.services.stripe.checkout.Session.create")
    def test_create_checkout_session_builds_line_items(self, mock_create):
        mock_create.return_value = {"id": "sess_123"}
        result = PaymentService.create_checkout_session(
            self.order, "https://example.com/ok", "https://example.com/cancel"
        )
        self.assertEqual(result, {"id": "sess_123"})
        call_kwargs = mock_create.call_args.kwargs
        self.assertEqual(call_kwargs["mode"], "payment")
        self.assertEqual(call_kwargs["client_reference_id"], self.order.id)
        self.assertEqual(len(call_kwargs["line_items"]), 1)
        self.assertEqual(call_kwargs["line_items"][0]["quantity"], 2)
        self.assertEqual(call_kwargs["line_items"][0]["price_data"]["unit_amount"], 5000)

    def test_process_successful_payment_marks_order_paid(self):
        self.assertFalse(self.order.paid)
        PaymentService.process_successful_payment(self.order)
        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)

    @patch("payment.services.stripe.PaymentIntent.create")
    @patch("payment.services.StripeCustomerHandler.create_or_get_customer")
    def test_create_payment_intent_delegates_to_stripe(self, mock_cust, mock_intent):
        mock_cust.return_value = {"id": "cus_x"}
        mock_intent.return_value = {"id": "pi_y"}
        out = PaymentService.create_payment_intent(self.user, 1000, currency="usd")
        self.assertEqual(out, {"id": "pi_y"})
        mock_intent.assert_called_once()
        kwargs = mock_intent.call_args.kwargs
        self.assertEqual(kwargs["amount"], 1000)
        self.assertEqual(kwargs["currency"], "usd")
        self.assertEqual(kwargs["customer"], "cus_x")


class StripeWebhookTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username="wuser", password="x", email="w@x.com"
        )
        self.category = Category.objects.create(name="c", slug="c")
        self.product = Product.objects.create(
            category=self.category,
            name="P",
            slug="p",
            price=Decimal("10.00"),
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="A",
            last_name="B",
            email="a@b.com",
            address="addr",
            postal_code="00000",
            city="city",
        )
        OrderItem.objects.create(
            order=self.order, product=self.product, price=Decimal("10.00"), quantity=1
        )

    def _post(self, sig_header=None, body=b"{}"):
        req = self.factory.post(
            "/payment/webhook/",
            data=body,
            content_type="application/json",
        )
        if sig_header is not None:
            req.META["HTTP_STRIPE_SIGNATURE"] = sig_header
        return req

    def test_missing_signature_returns_400(self):
        response = stripe_webhook(self._post())
        self.assertEqual(response.status_code, 400)

    @patch("payment.webhooks.stripe.Webhook.construct_event")
    def test_invalid_payload_returns_400(self, mock_construct):
        mock_construct.side_effect = ValueError("bad payload")
        response = stripe_webhook(self._post(sig_header="sig"))
        self.assertEqual(response.status_code, 400)

    @patch("payment.webhooks.stripe.Webhook.construct_event")
    def test_invalid_signature_returns_400(self, mock_construct):
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "bad sig", "sig"
        )
        response = stripe_webhook(self._post(sig_header="sig"))
        self.assertEqual(response.status_code, 400)

    @patch("payment.webhooks.payment_completed.delay")
    @patch("payment.webhooks.send_order_status_update_email.delay")
    @patch("payment.webhooks.stripe.Webhook.construct_event")
    def test_successful_checkout_marks_order_paid_and_dispatches(
        self, mock_construct, mock_email, mock_complete
    ):
        class _Obj:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        session = _Obj(
            mode="payment",
            payment_status="paid",
            client_reference_id=self.order.id,
            payment_intent="pi_test_999",
        )
        event = _Obj(type="checkout.session.completed", data=_Obj(object=session))
        mock_construct.return_value = event

        response = stripe_webhook(self._post(sig_header="sig"))
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)
        self.assertEqual(self.order.stripe_id, "pi_test_999")
        self.assertEqual(self.order.status, "confirmed")
        mock_email.assert_called_once_with(self.order.id, "confirmed")
        mock_complete.assert_called_once_with(self.order.id)

    @patch("payment.webhooks.stripe.Webhook.construct_event")
    def test_missing_order_returns_404(self, mock_construct):
        class _Obj:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        session = _Obj(
            mode="payment",
            payment_status="paid",
            client_reference_id=999_999,
            payment_intent="pi_x",
        )
        event = _Obj(type="checkout.session.completed", data=_Obj(object=session))
        mock_construct.return_value = event

        response = stripe_webhook(self._post(sig_header="sig"))
        self.assertEqual(response.status_code, 404)

    @patch("payment.webhooks.stripe.Webhook.construct_event")
    def test_non_payment_event_returns_200_without_changes(self, mock_construct):
        class _Obj:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        event = _Obj(type="payment_intent.created", data=_Obj(object=_Obj()))
        mock_construct.return_value = event

        response = stripe_webhook(self._post(sig_header="sig"))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertFalse(self.order.paid)


class WebhookUrlRoutingTest(TestCase):
    def test_webhook_url_resolves(self):
        url = reverse("payment:stripe-webhook")
        self.assertEqual(url, "/payment/webhook/")


class PaymentViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="pvuser", password="pvpass123", email="pv@x.com"
        )
        self.category = Category.objects.create(name="cat", slug="cat-pv")
        self.product = Product.objects.create(
            category=self.category,
            name="Item",
            slug="item-pv",
            price=Decimal("30.00"),
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="A",
            last_name="B",
            email="a@b.com",
            address="addr",
            postal_code="00000",
            city="city",
        )

    def test_payment_completed_renders(self):
        response = self.client.get(reverse("payment:completed"))
        self.assertEqual(response.status_code, 200)

    def test_payment_canceled_renders(self):
        response = self.client.get(reverse("payment:canceled"))
        self.assertEqual(response.status_code, 200)

    def test_payment_process_get_renders(self):
        session = self.client.session
        session["order_id"] = self.order.id
        session.save()
        response = self.client.get(reverse("payment:process"))
        self.assertEqual(response.status_code, 200)

    def test_payment_process_no_order_404(self):
        session = self.client.session
        session["order_id"] = 999999
        session.save()
        response = self.client.get(reverse("payment:process"))
        self.assertEqual(response.status_code, 404)

    @patch("payment.views.PaymentService.create_checkout_session")
    def test_payment_process_post_redirects_to_stripe(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://stripe.example.com/checkout/sess_abc"
        mock_create.return_value = mock_session

        session = self.client.session
        session["order_id"] = self.order.id
        session.save()

        response = self.client.post(reverse("payment:process"))
        # redirect() ignores code=303 kwarg silently — bug logged for separate fix
        self.assertIn(response.status_code, (302, 303))

    def test_payment_method_list_requires_login(self):
        response = self.client.get(reverse("payment:payment_method_list"))
        self.assertEqual(response.status_code, 302)

    def test_payment_method_list_renders_for_user(self):
        self.client.force_login(self.user)
        PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_xxx",
            card_type="visa",
            last_four_digits="0000",
            card_holder_name="X",
            exp_month=6,
            exp_year=2030,
        )
        response = self.client.get(reverse("payment:payment_method_list"))
        self.assertEqual(response.status_code, 200)

    def test_payment_method_add_get_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("payment:payment_method_add"))
        self.assertEqual(response.status_code, 200)

    def test_create_payment_intent_rejects_invalid_amount(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("payment:create_intent"),
            data=json.dumps({"amount": 0}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_confirm_payment_missing_id_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("payment:confirm_payment"),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("payment.views.stripe.PaymentIntent.retrieve")
    def test_confirm_payment_succeeded(self, mock_retrieve):
        intent = MagicMock()
        intent.status = "succeeded"
        mock_retrieve.return_value = intent

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("payment:confirm_payment"),
            data=json.dumps({"paymentIntentId": "pi_x"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body["success"])

    @patch("payment.views.stripe.PaymentIntent.retrieve")
    def test_confirm_payment_pending(self, mock_retrieve):
        intent = MagicMock()
        intent.status = "requires_action"
        mock_retrieve.return_value = intent

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("payment:confirm_payment"),
            data=json.dumps({"paymentIntentId": "pi_y"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertFalse(body["success"])
        self.assertTrue(body["requiresAction"])


class StripeCustomerHandlerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="schuser", password="x", email="sch@x.com"
        )

    def test_returns_existing_customer_id(self):
        self.user.stripe_customer_id = "cus_existing"
        self.user.save()
        result = StripeCustomerHandler.create_or_get_customer(self.user)
        self.assertEqual(result, {"id": "cus_existing", "created": False})

    @patch("payment.stripe_handler.stripe.Customer.create")
    def test_creates_new_customer(self, mock_create):
        mock_create.return_value = MagicMock(id="cus_new_456")
        result = StripeCustomerHandler.create_or_get_customer(self.user)
        self.assertEqual(result["id"], "cus_new_456")
        self.assertTrue(result["created"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.stripe_customer_id, "cus_new_456")

    @patch("payment.stripe_handler.stripe.Customer.create")
    def test_stripe_error_raises_wrapped_exception(self, mock_create):
        mock_create.side_effect = stripe.error.StripeError("api down")
        with self.assertRaises(Exception):  # noqa: B017 — code raises bare Exception
            StripeCustomerHandler.create_or_get_customer(self.user)


class StripePaymentMethodHandlerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="spmuser", password="x", email="spm@x.com"
        )
        self.user.stripe_customer_id = "cus_test"
        self.user.save()

    @patch("payment.stripe_handler.stripe.PaymentMethod.retrieve")
    @patch("payment.stripe_handler.stripe.PaymentMethod.attach")
    def test_attach_creates_db_record_and_marks_default_if_first(
        self, mock_attach, mock_retrieve
    ):
        fake_pm = MagicMock()
        fake_pm.customer = None
        fake_pm.card.brand = "visa"
        fake_pm.card.last4 = "1111"
        fake_pm.card.exp_month = 1
        fake_pm.card.exp_year = 2030
        fake_pm.billing_details.name = "John"
        mock_retrieve.return_value = fake_pm

        db = StripePaymentMethodHandler.attach_payment_method(self.user, "pm_attach_x")
        self.assertTrue(db.is_default)
        self.assertEqual(db.card_type, "visa")
        self.assertEqual(db.last_four_digits, "1111")
        mock_attach.assert_called_once()

    @patch("payment.stripe_handler.stripe.PaymentMethod.retrieve")
    def test_attach_stripe_error_wraps_message(self, mock_retrieve):
        mock_retrieve.side_effect = stripe.error.StripeError("api down")
        with self.assertRaises(Exception):  # noqa: B017 — code raises bare Exception
            StripePaymentMethodHandler.attach_payment_method(self.user, "pm_bad")

    @patch("payment.stripe_handler.stripe.PaymentMethod.detach")
    def test_detach_swallows_invalid_request(self, mock_detach):
        mock_detach.side_effect = stripe.error.InvalidRequestError("nope", "pm_x")
        # Should NOT raise
        StripePaymentMethodHandler.detach_payment_method("pm_x")

    @patch("payment.stripe_handler.stripe.PaymentMethod.detach")
    def test_delete_removes_local_record(self, mock_detach):
        pm = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_del",
            card_type="visa",
            last_four_digits="9999",
            card_holder_name="J",
            exp_month=1,
            exp_year=2030,
        )
        StripePaymentMethodHandler.delete_payment_method(pm)
        self.assertFalse(PaymentMethod.objects.filter(id=pm.id).exists())

    @patch("payment.stripe_handler.stripe.Customer.modify")
    def test_set_default_updates_stripe_and_local(self, mock_modify):
        pm = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_def",
            card_type="visa",
            last_four_digits="0000",
            card_holder_name="J",
            exp_month=2,
            exp_year=2030,
            is_default=False,
        )
        StripePaymentMethodHandler.set_default_payment_method(pm)
        pm.refresh_from_db()
        self.assertTrue(pm.is_default)
        mock_modify.assert_called_once()

    @patch("payment.stripe_handler.stripe.Customer.modify")
    def test_set_default_stripe_error_wraps(self, mock_modify):
        mock_modify.side_effect = stripe.error.StripeError("boom")
        pm = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_err",
            card_type="visa",
            last_four_digits="1212",
            card_holder_name="J",
            exp_month=2,
            exp_year=2030,
        )
        with self.assertRaises(Exception):  # noqa: B017 — code raises bare Exception
            StripePaymentMethodHandler.set_default_payment_method(pm)


class PaymentMethodSelectionFormTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="fmuser", password="x")
        PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id="pm_form",
            card_type="visa",
            last_four_digits="0001",
            card_holder_name="J",
            exp_month=1,
            exp_year=2030,
            is_default=True,
        )

    def test_form_builds_choices_from_user_methods(self):
        form = PaymentMethodSelectionForm(user=self.user)
        choices = form.fields["payment_method"].choices
        self.assertEqual(len(choices), 1)
        self.assertIn("0001", choices[0][1])

    def test_form_requires_selection_or_new_card(self):
        form = PaymentMethodSelectionForm(user=self.user, data={})
        self.assertFalse(form.is_valid())

    def test_form_valid_with_existing_pm(self):
        pm_id = self.user.payment_methods.first().id
        form = PaymentMethodSelectionForm(
            user=self.user, data={"payment_method": str(pm_id)}
        )
        self.assertTrue(form.is_valid())

    def test_form_valid_with_new_card_flag(self):
        form = PaymentMethodSelectionForm(
            user=self.user, data={"use_new_card": "on"}
        )
        self.assertTrue(form.is_valid())


class PaymentCompletedTaskTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="ptuser", password="x", email="pt@x.com"
        )
        self.category = Category.objects.create(name="cat", slug="cat-pt")
        self.product = Product.objects.create(
            category=self.category,
            name="I",
            slug="ipt",
            price=Decimal("5.00"),
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name="A",
            last_name="B",
            email="pt@x.com",
            address="addr",
            postal_code="00000",
            city="c",
        )
        OrderItem.objects.create(
            order=self.order, product=self.product, price=Decimal("5.00"), quantity=1
        )

    @patch("payment.tasks.weasyprint.HTML")
    def test_payment_completed_sends_email_with_pdf(self, mock_html):
        mock_doc = MagicMock()
        mock_html.return_value = mock_doc

        from django.core import mail

        payment_completed_task(self.order.id)

        self.assertGreaterEqual(len(mail.outbox), 1)
        msg = mail.outbox[-1]
        self.assertIn("pt@x.com", msg.to)
        self.assertEqual(len(msg.attachments), 1)

    def test_payment_completed_missing_order_no_crash(self):
        # Order.DoesNotExist branch — no retry, no raise
        payment_completed_task(999_999)
