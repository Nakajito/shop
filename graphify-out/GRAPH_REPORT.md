# Graph Report - .  (2026-08-01)

## Corpus Check
- Large corpus: 325 files · ~3,085,770 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 1359 nodes · 1988 edges · 161 communities (92 shown, 69 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 428 edges (avg confidence: 0.69)
- Token cost: 340,869 input · 0 output

## Community Hubs (Navigation)
- Blog Management View Tests
- Storefront Templates & Favorites UX
- Coupon Model, Form & Admin
- Order & Address Service Layer
- Orders Admin Inlines
- Shop Model & View Tests
- Project URLs & Error Views
- Support Ticket Tests
- Support Ticket Model & Forms
- Order Templates & Emails
- Order & Address Model Tests
- Address Model, Form & Views
- CustomUser Model & Enums
- Cart Pricing & Checkout Integration
- Blog Forms (Post, Category, Tag)
- Order Celery Tasks & Signals
- Shop Admin (Category, Product)
- User Types & Profile Signals
- Accounts View Tests
- Session Cart & Cart Tests
- Order Model Behaviour
- Accounts Admin & UserProfile
- DeepL translate_text Tests
- Architecture Concepts (CLAUDE.md)
- Stripe Payment Method Handler
- TranslationCache Model
- Order Managers & QuerySets
- Order Lifecycle Views
- PaymentMethod Model & Views
- Allauth Adapters & Social Login
- PaymentService (Stripe Checkout)
- Payment View Tests
- Redis Recommender
- get_translation Pipeline Tests
- Blog Admin & Post Media Models
- safe_next_url Redirect Guard
- Shop Views & Catalog
- i18n Filters & Blog Manage Templates
- i18n_extras Template Filters
- Support Admin
- CI Pipeline & Working Preferences
- Blog Category & Tag Models
- Cart Forms & Views
- Order PDF & Admin Views
- Payment Method Selection Form
- seed_demo Command
- Product Manager & QuerySet
- Support Ticket Manager
- Settings, Routing & Error Docs
- Profile Forms & View
- User Registration
- Accounts Views (logout, user type)
- Blog Public & Manage Views
- Post QuerySet
- Post Manager
- Product Model & Favorites
- Order Admin Links
- Address View Tests
- PaymentMethod Admin
- Stripe Elements Script (payment)
- Stripe Customer & Webhook Tests
- Stripe Customer Handler Tests
- translate_po Command
- Stripe Elements Script (static)
- Support View Coverage Tests
- Media Serving & Refactor Phases 2-4
- Test Baseline & Deferrals
- Login Form & View
- Login View Tests
- Post Model & Delete View
- Cart Mutation Methods
- PaymentMethod Model Tests
- Account Deactivation
- PostVideo Embeds
- Blog Template Tags
- Cart Context Processor
- Shop Cache Signals & Recommender Loader
- Pre-commit & Refactor Phases 0-1
- Accounts AppConfig
- Settings Package
- setup_google_oauth Command
- Orders AppConfig
- Shop AppConfig
- TicketMessage Tests
- Cart AppConfig
- Coupons AppConfig
- Payment AppConfig
- Payment Method Add (Stripe Elements)
- Carousel Autoplay Helpers
- Blog AppConfig
- blog.js Formset Rows (app)
- manage.py Entrypoint
- blog.js Formset Rows (collected)
- Support AppConfig
- Accounts __init__.py
- Accounts __init__.py
- Accounts Migrations
- Accounts Migrations
- Accounts Migrations
- Accounts Migrations
- Accounts Migrations
- Accounts Migrations
- Accounts Migrations
- Blog Migrations
- Cart coupon property
- Cart __init__
- Cart __len__
- Coupons Migrations
- Coupons Migrations
- Coupons Migrations
- Coupons Migrations
- ASGI Config
- WSGI Config
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Orders Migrations
- Payment Migrations
- Payment Migrations
- Shop Migrations
- Shop Migrations
- Shop Migrations
- Shop Migrations
- Shop Migrations
- Shop Migrations
- Shop Migrations
- Shop Migrations
- Mobile Drawer Menu
- getCookie CSRF Readers
- Support Migrations
- Support Migrations
- pyproject.toml module

## God Nodes (most connected - your core abstractions)
1. `CustomUser` - 72 edges
2. `Cart` - 41 edges
3. `Order` - 31 edges
4. `UserProfile` - 21 edges
5. `Address` - 21 edges
6. `CartTest` - 20 edges
7. `PaymentViewsTest` - 18 edges
8. `PostManager` - 17 edges
9. `BlogManagementViewTests` - 17 edges
10. `StripePaymentMethodHandler` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Per-phase baseline gate (no regressions allowed)` --semantically_similar_to--> `Refactoring Plan — One Synk (myshop)`  [INFERRED] [semantically similar]
  BASELINE.md → REFACTORING_PLAN.md
- `Ruff pre-commit hook (lint + format)` --semantically_similar_to--> `CI Pipeline — Django tests + lint`  [INFERRED] [semantically similar]
  .pre-commit-config.yaml → .github/workflows/ci.yml
- `Split media serving (static() under DEBUG, re_path otherwise)` --semantically_similar_to--> `Django static() returns [] when DEBUG=False`  [INFERRED] [semantically similar]
  CLAUDE.md → AGENTS.md
- `Translations — two layers (static .po + DB |tr)` --semantically_similar_to--> `Two-layer i18n translation system`  [INFERRED] [semantically similar]
  CLAUDE.md → AGENTS.md
- `Pre-existing BlogPublicViewTests failures (4)` --references--> `Public blog post list (Recetario) template`  [AMBIGUOUS]
  BASELINE.md → myshop/blog/templates/blog/post_list.html

## Import Cycles
- 1-file cycle: `myshop/myshop/celery.py -> myshop/myshop/celery.py`

## Hyperedges (group relationships)
- **Blog post management flow (dashboard → list → form → delete)** — myshop_blog_templates_blog_manage_dashboard_blog_dashboard, myshop_blog_templates_blog_manage_post_list_manage_post_list_page, myshop_blog_templates_blog_manage_post_form_post_form_page, myshop_blog_templates_blog_manage_post_confirm_delete_post_delete_page, myshop_blog_templates_blog_manage_post_form_blog_ajax_urls [INFERRED 0.85]
- **Address book CRUD flow (profile → list → form/delete → AddressService)** — myshop_accounts_templates_accounts_profile_profile_page, myshop_orders_templates_orders_addresses_list_address_list_page, myshop_orders_templates_orders_addresses_form_address_form_page, myshop_orders_templates_orders_addresses_confirm_delete_address_delete_page, claude_service_layer [INFERRED 0.85]
- **Dual-layer i18n (static .po + |tr DeepL-cached DB content)** — agents_translation_system, agents_tr_filter, agents_translation_cache, claude_translation_layers, myshop_blog_templates_blog_post_detail_post_detail_page, myshop_cart_templates_cart_detail_cart_detail_page, myshop_blog_templates_blog_post_list_recetario_page [INFERRED 0.85]
- **Order fulfillment and tracking view set (history, detail, tracking timeline, shipment info, status audit log, invoice)** — myshop_orders_templates_orders_order_order_history_order_history_html, myshop_orders_templates_orders_order_order_detail_order_detail_html, myshop_orders_templates_orders_order_order_tracking_order_tracking_html, myshop_orders_templates_orders_order_order_tracking_info_order_tracking_info_html, myshop_orders_templates_orders_order_order_status_history_order_status_history_html, myshop_orders_templates_orders_order_pdf_pdf_html [INFERRED 0.85]
- **Order notification email templates (HTML + plain-text alternatives for status update and shipment tracking)** — myshop_orders_templates_orders_emails_order_status_update_order_status_update_html, myshop_orders_templates_orders_emails_order_status_update_order_status_update_txt, myshop_orders_templates_orders_emails_order_tracking_order_tracking_html, myshop_orders_templates_orders_emails_order_tracking_order_tracking_txt [EXTRACTED 1.00]
- **Saved payment method (wallet) management flow: navbar entry, list, add via Stripe, delete confirmation, reuse at checkout** — myshop_shop_templates_includes_navbar_navbar_html, myshop_payment_templates_payment_payment_methods_list_list_html, myshop_payment_templates_payment_payment_methods_add_add_html, myshop_payment_templates_payment_payment_methods_confirm_delete_confirm_delete_html, myshop_orders_templates_orders_order_create_create_html [INFERRED 0.85]
- **Favorites Toggle Flow (list, detail, favorites page, AJAX contract)** — myshop_shop_templates_shop_product_list_product_list, myshop_shop_templates_shop_product_detail_product_detail, myshop_shop_templates_shop_product_favorites_favorites_page, myshop_shop_templates_shop_product_detail_favorite_toggle_ajax, myshop_shop_templates_shop_product_list_user_favorites_context [INFERRED 0.95]
- **Branded HTTP Error Page Family** — myshop_templates_400_bad_request_page, myshop_templates_403_forbidden_page, myshop_templates_404_not_found_page, myshop_templates_500_server_error_page, myshop_templates_502_bad_gateway_page, myshop_templates_500_error_page_context_hazard [EXTRACTED 1.00]
- **Support Ticket Lifecycle Surfaces (create, list, detail, reply/close)** — myshop_support_templates_support_ticket_form_ticket_form, myshop_support_templates_support_ticket_list_ticket_list, myshop_support_templates_support_ticket_detail_ticket_detail, myshop_support_templates_support_ticket_detail_status_lifecycle, myshop_shop_templates_includes_sidebar_account_sidebar [INFERRED 0.95]

## Communities (161 total, 69 thin omitted)

### Community 0 - "Blog Management View Tests"
Cohesion: 0.05
Nodes (5): BlogManagementViewTests, BlogManagerTests, BlogModelTests, BlogPublicViewTests, TestCase

### Community 1 - "Storefront Templates & Favorites UX"
Cohesion: 0.08
Nodes (37): Account Sidebar Navigation, Resolver-Match Active Link Highlighting, Synk Food Base Template, Flash Message Auto-Dismiss and bfcache Reload, Multi-Brand Split: Synk Food vs Synk Beauty, One Synk Corporate Landing Page, Favorite Toggle AJAX Contract, Product Detail Page (+29 more)

### Community 2 - "Coupon Model, Form & Admin"
Cohesion: 0.08
Nodes (14): CouponAdmin, Administration interface for the Coupon model.      Optimizations:     - list_ed, CouponApplyForm, Normalize the coupon code by stripping whitespace.         This prevents ' SUMME, Form to allow users to input and submit a coupon code.      This form is typical, Coupon, Custom validation to ensure the date range is logical.         Django admin call, Model representing a discount coupon.      This model stores the code users must (+6 more)

### Community 3 - "Order & Address Service Layer"
Cohesion: 0.09
Nodes (14): OrderCreateForm, Form for creating a new Order during checkout.      This ModelForm handles the e, AddressService, OrderService, Create an order from a shopping cart and form data., Cancel an order and initiate refund if paid., Return a summary dict with order calculations., Set an address as default (model save handles unsetting others). (+6 more)

### Community 4 - "Orders Admin Inlines"
Cohesion: 0.10
Nodes (17): AddressAdmin, OrderItemsInline, OrderStatusUpdateAdmin, OrderStatusUpdateInline, OrderTrackingAdmin, OrderTrackingInline, Admin to manage shipping addresses., Admin to manage tracking information independently. (+9 more)

### Community 5 - "Shop Model & View Tests"
Cohesion: 0.08
Nodes (8): CategoryModelTest, ProductDetailViewTest, ProductListViewTest, ProductManagerTest, ProductModelTest, TestCase, Gallery renders one slide (active) and no arrows/dots., Gallery renders slides, arrows, and dots when images exist.

### Community 6 - "Project URLs & Error Views"
Cohesion: 0.13
Nodes (16): HttpRequest, HttpResponse, Main URL configuration for the 'myshop' project.  Central routing hub. Delegates, bad_gateway(), bad_request(), maintenance(), page_not_found(), permission_denied() (+8 more)

### Community 7 - "Support Ticket Tests"
Cohesion: 0.09
Nodes (7): TestCase, SupportTicketManagerTest, SupportTicketModelTest, TicketCloseViewTest, TicketDetailViewTest, TicketListViewTest, TicketReplyViewTest

### Community 8 - "Support Ticket Model & Forms"
Cohesion: 0.09
Nodes (18): Meta, Form for users to add replies to an existing ticket., Form for customers to create new support tickets., SupportTicketForm, TicketMessageForm, Returns Bootstrap 5 context class for the status badge., Model for customer support tickets.     Handles issue reporting, clarifications,, SupportTicket (+10 more)

### Community 9 - "Order Templates & Emails"
Cohesion: 0.13
Nodes (25): Order Status Update Email (HTML), Order Status Update Email (Plain Text), Order Shipped Tracking Email (HTML), Order Shipped Tracking Email (Plain Text), Cancel Order Confirmation Page, Checkout / Order Create Page, Order Confirmed Page, Order Action Center (reorder, buy again, cancel, invoice, track) (+17 more)

### Community 10 - "Order & Address Model Tests"
Cohesion: 0.09
Nodes (7): AddressModelTest, CancelOrderViewTest, OrderHistoryViewTest, OrderItemModelTest, OrderManagerTest, TestCase, POST to cancel an unpaid order should mark it cancelled and create a status upda

### Community 11 - "Address Model, Form & Views"
Cohesion: 0.12
Nodes (18): AddressForm, Meta, Form to create or edit shipping addresses.      This form handles user input for, Address, Return the formatted full address string., Model representing a user's shipping or billing address., address_create(), address_delete() (+10 more)

### Community 12 - "CustomUser Model & Enums"
Cohesion: 0.10
Nodes (17): AbstractUser, CustomUser, Custom user model extending Django's AbstractUser.      This model serves as the, Check if the user has the Wholesaler role., Check if the user has the Regular User role., AddressType, Carrier, Meta (+9 more)

### Community 13 - "Cart Pricing & Checkout Integration"
Cohesion: 0.12
Nodes (7): Decimal, Calculate the monetary value of the discount based on the active coupon., Calculate the final total price after applying the coupon discount.          Ret, CheckoutFlowIntegrationTest, TestCase, Integration test for cart -> checkout -> order creation flow., OrderModelTest

### Community 14 - "Blog Forms (Post, Category, Tag)"
Cohesion: 0.11
Nodes (19): CategoryForm, Meta, PostForm, PostImageForm, PostVideoForm, Quick form for creating a new blog category inline., Form for adding images to a post gallery., Form for adding videos to a post. (+11 more)

### Community 15 - "Order Celery Tasks & Signals"
Cohesion: 0.14
Nodes (12): Dispatch tracking email when a new OrderTracking record is created., tracking_created(), order_created(), Send an email with tracking information when an order is shipped., Send an email notification when an order is created., Send an email notifying the customer of an order status change., send_order_status_update_email(), send_order_tracking_email() (+4 more)

### Community 16 - "Shop Admin (Category, Product)"
Cohesion: 0.11
Nodes (15): CategoryAdmin, ProductAdmin, ProductImageInline, Renders a small thumbnail for the product list view., Renders a small thumbnail for the inline image., Administration interface for product categories., Renders a small thumbnail for the category image., Displays the number of products in this category. (+7 more)

### Community 17 - "User Types & Profile Signals"
Cohesion: 0.13
Nodes (9): Meta, Enumeration for User Types to avoid magic strings., UserTypes, manage_user_profile(), Signal receiver that handles the creation and updates of UserProfiles.      This, confirm_payment(), payment_method_list(), AJAX endpoint to verify PaymentIntent status after frontend processing. (+1 more)

### Community 18 - "Accounts View Tests"
Cohesion: 0.12
Nodes (6): ChangeUserTypeViewTest, LogoutViewTest, ProfileViewTest, TestCase, RegisterViewTest, UserProfileModelTest

### Community 19 - "Session Cart & Cart Tests"
Cohesion: 0.26
Nodes (4): Cart, A session-based shopping cart management class.      This class handles the addi, CartTest, TestCase

### Community 20 - "Order Model Behaviour"
Cohesion: 0.12
Nodes (10): Order, Ensure only one address is marked as default per user., Model representing a customer order.     Includes snapshots of shipping data, pa, Sum of all items before discount., Calculate discount amount., Generate link to Stripe dashboard based on environment., Returns steps for the frontend timeline visualization., Updates the order status and creates a tracking log entry. (+2 more)

### Community 21 - "Accounts Admin & UserProfile"
Cohesion: 0.12
Nodes (10): BaseUserAdmin, CustomUserAdmin, Admin interface configuration for the CustomUser model.      Optimizations:, Defines the inline admin interface for the UserProfile model.      Best Practice, Admin interface configuration for the UserProfile model.      Performance:     -, UserProfileAdmin, UserProfileInline, Data model for extended user profile information.      Establishes a one-to-one (+2 more)

### Community 22 - "DeepL translate_text Tests"
Cohesion: 0.15
Nodes (11): Tests for the dynamic translation system (DeepL + TranslationCache).  Covers: -, Enables tag_handling=html when text contains HTML tags., Returns original text when the API raises an exception., Tests for the translate_text() function (DeepL API wrapper)., When no API key is configured, returns the original text., Uses free endpoint when key ends with :fx., Uses pro endpoint when key does NOT end with :fx., TranslateTextTests (+3 more)

### Community 23 - "Architecture Concepts (CLAUDE.md)"
Cohesion: 0.17
Nodes (18): AJAX add-to-cart (data-ajax-add / .js-add-cart-btn), AJAX favorites — live navbar badge (skUpdateFavBadge), Celery for email and PDF side-effects, accounts.CustomUser with regular/wholesaler user_type, Per-app managers.py query optimisation (with_full_details), Redis sorted-set recommender with silent degradation, Service layer (OrderService / AddressService / PaymentService), Session-based cart (CART_SESSION_ID, coupon_id in session) (+10 more)

### Community 24 - "Stripe Payment Method Handler"
Cohesion: 0.16
Nodes (7): Safely disconnects a card from Stripe., Removes card from Stripe and deletes local database record., Updates the Stripe Customer's default payment method settings., Handles logic for attaching, detaching, and defaulting cards via Stripe., Links a Stripe PaymentMethod (pm_...) to a Customer and saves it locally., StripePaymentMethodHandler, StripePaymentMethodHandlerTest

### Community 25 - "TranslationCache Model"
Cohesion: 0.18
Nodes (7): Persistent cache of dynamic (database) content translations., TranslationCache, Unit tests for the TranslationCache model., Same text always produces the same hash., Stored translations can be retrieved via get_cached., Storing the same text+langs again updates the translation., TranslationCacheModelTests

### Community 27 - "Order Lifecycle Views"
Cohesion: 0.13
Nodes (16): get_user_order(), Return the order if it belongs to the authenticated request user., buy_order(), cancel_order(), order_status_history(), order_tracking(), order_tracking_info(), Customer-facing tracking with timeline + status history. (+8 more)

### Community 28 - "PaymentMethod Model & Views"
Cohesion: 0.13
Nodes (10): PaymentMethod, Returns the formatted expiration date (e.g., 08/27)., Ensures only one payment method is marked as default per user., Returns the visually standard masked card (e.g., •••• 4242)., Model for storing user-saved payment methods (credit/debit cards).      We store, Returns True if the card expiration date has passed., payment_method_delete(), payment_method_set_default() (+2 more)

### Community 29 - "Allauth Adapters & Social Login"
Cohesion: 0.20
Nodes (6): DefaultAccountAdapter, DefaultSocialAccountAdapter, CustomAccountAdapter, CustomSocialAccountAdapter, Block social login for deactivated accounts., SocialAdapterTest

### Community 30 - "PaymentService (Stripe Checkout)"
Cohesion: 0.16
Nodes (6): PaymentService, Create a Stripe Checkout Session for the given order., Mark order as paid after successful payment., Vault a new payment method for a user., Create a Stripe PaymentIntent., PaymentServiceTest

### Community 32 - "Redis Recommender"
Cohesion: 0.21
Nodes (9): Command, BaseCommand, _get_redis(), Get a Redis connection, returning None if unavailable., A product recommendation engine based on 'Frequently Bought Together' logic., Generates the Redis key for a specific product's set., Records that a list of products were purchased together.         Uses a Pipeline, Clears all recommendation data from Redis. (+1 more)

### Community 33 - "get_translation Pipeline Tests"
Cohesion: 0.20
Nodes (8): GetTranslationTests, Tests for the get_translation() pipeline., When target language == source language, returns text as-is., On cache miss, calls DeepL and stores in TranslationCache., When cached, returns cached value without calling DeepL., Uses Django's active language when target_lang is None., get_translation(), Return cached/dynamic translation of ``text`` for the active language.      When

### Community 34 - "Blog Admin & Post Media Models"
Cohesion: 0.15
Nodes (10): CategoryAdmin, PostAdmin, PostImageInline, PostVideoInline, TagAdmin, Meta, PostImage, Gallery image attached to a blog post. (+2 more)

### Community 35 - "safe_next_url Redirect Guard"
Cohesion: 0.22
Nodes (5): TestCase, SafeNextUrlTest, Project-wide utility helpers (no Django app — pure functions)., Return ``?next=`` (or ``next`` POST field) only if same-host + scheme.      Prev, safe_next_url()

### Community 36 - "Shop Views & Catalog"
Cohesion: 0.15
Nodes (8): favorite_list(), form_mayorista(), product_detail(), product_list(), Displays the wholesaler contact form., Display all products in the user's favorites., Displays the product catalog with optional category filtering.     Optimized wit, Displays single product details, the cart form, and Redis recommendations.

### Community 37 - "i18n Filters & Blog Manage Templates"
Cohesion: 0.29
Nodes (12): |tr and |tr_safe template filters (i18n_extras), TranslationCache + DeepL cached translation, Two-layer i18n translation system, Translations — two layers (static .po + DB |tr), Blog manage dashboard template, window.BLOG_AJAX_URLS — inline AJAX category/tag creation, Blog post create/edit form template, Blog manage post list template (filters + pagination) (+4 more)

### Community 38 - "i18n_extras Template Filters"
Cohesion: 0.21
Nodes (7): Dynamically translate database content to the active language.      Spanish (sou, Like :func:`tr` but marks the result as safe HTML., tr(), tr_safe(), TestCase, Tests for the |tr and |tr_safe template filters., TemplateFilterTests

### Community 39 - "Support Admin"
Cohesion: 0.17
Nodes (8): Admin interface for managing support tickets and customer issues., Renders a color-coded badge based on ticket status., Highlights high-priority tickets., Standalone admin for auditing individual ticket messages., Displays ticket messages inline within the SupportTicket detail view., SupportTicketAdmin, TicketMessageAdmin, TicketMessageInline

### Community 40 - "CI Pipeline & Working Preferences"
Cohesion: 0.24
Nodes (11): CI Pipeline — Django tests + lint, Coverage gate --fail-under=78, WeasyPrint system dependency install step, Ruff pre-commit hook (lint + format), Working preferences (plan mode, TDD, task management, stack defaults), Mono-repo shape (tooling at root, Django under myshop/), myshop.utils.safe_next_url for ?next= redirects, Fase 5 — Reinforced tests, 80%+ coverage, CI (+3 more)

### Community 41 - "Blog Category & Tag Models"
Cohesion: 0.20
Nodes (6): Category, Blog category, separate from shop categories., Blog tag for flexible content classification., Tag, post_list(), List published blog posts with filtering by category, tag, date, and search.

### Community 42 - "Cart Forms & Views"
Cohesion: 0.27
Nodes (6): CartAddProductForm, Form for adding products to the cart or updating existing quantities.      Attri, cart_add(), cart_detail(), View to add a product to the cart or update its quantity.      Uses POST method, View to display the current contents of the shopping cart.      Optimizations:

### Community 43 - "Order PDF & Admin Views"
Cohesion: 0.24
Nodes (9): admin_order_detail(), admin_order_pdf(), order_pdf(), PDF receipt + staff admin-detail views for orders., Render the invoice PDF template and return it as an HTTP response., Staff-only internal order summary., Staff-side invoice PDF (inline disposition)., Customer receipt PDF download. (+1 more)

### Community 44 - "Payment Method Selection Form"
Cohesion: 0.27
Nodes (3): PaymentMethodSelectionForm, Form to select an existing payment method during the checkout process., PaymentMethodSelectionFormTest

### Community 48 - "Settings, Routing & Error Docs"
Cohesion: 0.22
Nodes (9): Dummy Stripe/email env injection in CI, Custom error handlers and the 502 limitation, handler400/403/404/500 branded error templates, i18n_patterns URL routing with deliberate exclusions, Settings package (base + development/production/testing), Environment selection via DJANGO_SETTINGS_MODULE, One Synk — Korean food store (myshop README), Main URL map (shop/cart/orders/payment/coupons/support/blog/accounts) (+1 more)

### Community 49 - "Profile Forms & View"
Cohesion: 0.25
Nodes (8): CustomUserChangeForm, Meta, Form for editing user account details (excluding password)., Form for updating the extended UserProfile (Bio, Avatar, etc)., UserProfileForm, profile(), User profile view.     GET: Display profile dashboard and edit forms.     POST:, UserChangeForm

### Community 50 - "User Registration"
Cohesion: 0.22
Nodes (7): CustomUserCreationForm, Form for registering new users.     Extends Django's UserCreationForm to include, Validate that the email is not already registered., Save the user instance.         Note: UserCreationForm.save() handles password h, New user registration view.     GET: Displays registration form.     POST: Proce, register(), UserCreationForm

### Community 51 - "Accounts Views (logout, user type)"
Cohesion: 0.22
Nodes (8): change_user_type(), google_login(), profile_details(), View to log out.     Only accepts POST for security (prevents CSRF attacks via G, Profile details view (read-only).     Displays summary information about the use, View to switch between normal user and wholesaler., Redirect to Google OAuth2 login endpoint.     This path usually comes from djang, user_logout()

### Community 52 - "Blog Public & Manage Views"
Cohesion: 0.22
Nodes (6): manage_dashboard(), manage_post_list(), post_detail(), Blog management dashboard with post statistics., List all posts with search and status filter., Display a single published blog post with gallery, videos, and related posts.

### Community 55 - "Product Model & Favorites"
Cohesion: 0.22
Nodes (7): cart_remove(), View to remove a product from the cart., Product, Model representing an item for sale in the shop., Return the canonical URL for the product detail view., Toggle a product in the user's favorites list. Returns JSON., toggle_favorite()

### Community 56 - "Order Admin Links"
Cohesion: 0.22
Nodes (5): OrderAdmin, Link to Stripe Dashboard if applicable., Link to custom order detail view., Link to download PDF invoice., Administration interface for the Order model.      Features:     - Lists essenti

### Community 58 - "PaymentMethod Admin"
Cohesion: 0.22
Nodes (5): PaymentMethodAdmin, Displays a boolean icon if the card is past its expiry date., Prevents manual card addition.         Cards must be added via the frontend to b, Allows removal, but use with caution as it affects recurring logic., Admin configuration to manage user payment methods.      Registration/Addition i

### Community 59 - "Stripe Elements Script (payment)"
Cohesion: 0.22
Nodes (7): cardElement, cvcElement, elements, expiryElement, form, stripe, submitButton

### Community 60 - "Stripe Customer & Webhook Tests"
Cohesion: 0.25
Nodes (5): Manages Stripe Customer objects and links them to CustomUser instances., StripeCustomerHandler, PaymentCompletedTaskTest, TestCase, WebhookUrlRoutingTest

### Community 61 - "Stripe Customer Handler Tests"
Cohesion: 0.28
Nodes (4): Retrieves an existing Stripe customer ID or creates a new one.          Returns:, StripeCustomerHandlerTest, create_payment_intent(), AJAX endpoint to generate a PaymentIntent client secret.

### Community 62 - "translate_po Command"
Cohesion: 0.22
Nodes (5): Command, BaseCommand, main(), Make sure every placeholder from *original* appears in *translated*.      DeepL, _restore_placeholders()

### Community 63 - "Stripe Elements Script (static)"
Cohesion: 0.22
Nodes (7): cardElement, cvcElement, elements, expiryElement, form, stripe, submitButton

### Community 65 - "Media Serving & Refactor Phases 2-4"
Cohesion: 0.25
Nodes (8): Coolify + Docker persistent volume MEDIA_ROOT, Django static() returns [] when DEBUG=False, Split media serving (static() under DEBUG, re_path otherwise), orders/views as a package with re-exporting __init__, Always-on media re_path security risk, Fase 2 — Settings & configuration single source of truth, Fase 3 — App reorganisation (views/tests packages), Fase 4 — DRY in code (mixins, validators, partials)

### Community 66 - "Test Baseline & Deferrals"
Cohesion: 0.36
Nodes (8): Pre-existing BlogPublicViewTests failures (4), CheckConstraint(check=) → condition= (Django 6), Per-phase baseline gate (no regressions allowed), Test baseline — pre-refactor (tag pre-refactor-2026-05-25), Project docs index (AGENTS / BASELINE / REFACTORING_PLAN / tasks), .codegraph/codegraph.db symbol index, Documented deferrals after the refactor, Refactoring Plan — One Synk (myshop)

### Community 67 - "Login Form & View"
Cohesion: 0.25
Nodes (6): CustomUserLoginForm, Authentication form allowing login via Username OR Email., Authenticate the user against the database.         Checks for deactivated accou, Helper to retrieve the authenticated user object., User login view.     GET: Displays login form.     POST: Authenticates user and, user_login()

### Community 69 - "Post Model & Delete View"
Cohesion: 0.25
Nodes (5): Post, Return manually selected related posts. If none exist,         fall back to post, Blog post with rich text content, gallery, and video support., manage_post_delete(), Delete a blog post with confirmation.

### Community 70 - "Cart Mutation Methods"
Cohesion: 0.25
Nodes (3): Iterate over the items in the cart and get the products from the database., Add a product to the cart or update its quantity., Remove a product from the cart.

### Community 72 - "Account Deactivation"
Cohesion: 0.29
Nodes (4): DeactivateAccountForm, Form requiring password confirmation to deactivate the account., deactivate_account(), Soft-delete: sets is_active=False and logs the user out.     Requires password c

### Community 73 - "PostVideo Embeds"
Cohesion: 0.33
Nodes (4): PostVideo, Video attached to a blog post -- supports YouTube, Vimeo, or file upload., Convert YouTube/Vimeo URLs to embeddable format., Extract video ID from various YouTube URL formats.

### Community 74 - "Blog Template Tags"
Cohesion: 0.29
Nodes (6): blog_categories(), blog_tags(), Return the N most recent published posts., Return all blog categories., Return all blog tags., recent_posts()

### Community 75 - "Cart Context Processor"
Cohesion: 0.29
Nodes (3): cart(), Context processor to make the Cart object available in all templates.      This, Meta

### Community 77 - "Pre-commit & Refactor Phases 0-1"
Cohesion: 0.33
Nodes (6): djLint Django template hook, pre-commit hook set, collectstatic output and db.sqlite3 tracked in git, Dead/duplicate files finding (_copia, _ORIGINAL, main.py, products/), Fase 0 — Baseline & safety net (blocking), Fase 1 — Zero-risk cleanup

### Community 78 - "Accounts AppConfig"
Cohesion: 0.33
Nodes (4): AccountsConfig, AppConfig, Perform initialization tasks when the application is ready.          This method, Configuration class for the 'accounts' application.      This class sets up appl

### Community 81 - "Orders AppConfig"
Cohesion: 0.40
Nodes (3): OrdersConfig, AppConfig, Configuration class for the 'orders' application.      This class manages metada

### Community 82 - "Shop AppConfig"
Cohesion: 0.40
Nodes (3): AppConfig, Configuration class for the 'shop' application.      This class manages the meta, ShopConfig

### Community 85 - "Cart AppConfig"
Cohesion: 0.50
Nodes (3): CartConfig, AppConfig, Configuration class for the 'cart' application.      This class defines applicat

### Community 86 - "Coupons AppConfig"
Cohesion: 0.50
Nodes (3): CouponsConfig, AppConfig, Configuration class for the 'coupons' application.      This class manages metad

### Community 87 - "Payment AppConfig"
Cohesion: 0.50
Nodes (3): PaymentConfig, AppConfig, Configuration class for the 'payment' application.      This class manages metad

### Community 88 - "Payment Method Add (Stripe Elements)"
Cohesion: 0.50
Nodes (4): PaymentMethodForm, Form to add a payment card using Stripe Elements.      IMPORTANT: Sensitive data, payment_method_add(), Vaults a new card using Stripe Elements payment_method_id.

### Community 89 - "Carousel Autoplay Helpers"
Cohesion: 0.50
Nodes (4): goTo (product gallery carousel), goTo (hero carousel), resetAuto (restart autoplay after interaction), startAuto (carousel autoplay)

## Ambiguous Edges - Review These
- `Pre-existing BlogPublicViewTests failures (4)` → `Public blog post list (Recetario) template`  [AMBIGUOUS]
  BASELINE.md · relation: references
- `Mono-repo shape (tooling at root, Django under myshop/)` → `One Synk — shop (repo README)`  [AMBIGUOUS]
  README.md · relation: references

## Knowledge Gaps
- **92 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+87 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **69 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Pre-existing BlogPublicViewTests failures (4)` and `Public blog post list (Recetario) template`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Mono-repo shape (tooling at root, Django under myshop/)` and `One Synk — shop (repo README)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `CustomUser` connect `CustomUser Model & Enums` to `Order & Address Service Layer`, `Orders Admin Inlines`, `Project URLs & Error Views`, `Support Ticket Tests`, `Support Ticket Model & Forms`, `Order & Address Model Tests`, `Address Model, Form & Views`, `Cart Pricing & Checkout Integration`, `User Types & Profile Signals`, `Accounts View Tests`, `Order Model Behaviour`, `Accounts Admin & UserProfile`, `Stripe Payment Method Handler`, `PaymentMethod Model & Views`, `Allauth Adapters & Social Login`, `PaymentService (Stripe Checkout)`, `Payment View Tests`, `Payment Method Selection Form`, `Profile Forms & View`, `User Registration`, `Address View Tests`, `Stripe Customer & Webhook Tests`, `Stripe Customer Handler Tests`, `Support View Coverage Tests`, `Login Form & View`, `Login View Tests`, `PaymentMethod Model Tests`, `Account Deactivation`, `TicketMessage Tests`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `Order` connect `Order Model Behaviour` to `Order & Address Service Layer`, `Orders Admin Inlines`, `Support Ticket Model & Forms`, `Address Model, Form & Views`, `CustomUser Model & Enums`, `Order PDF & Admin Views`, `Order Celery Tasks & Signals`, `Order Admin Links`, `Order Lifecycle Views`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `Cart` connect `Session Cart & Cart Tests` to `Order & Address Service Layer`, `Cart Mutation Methods`, `Cart coupon property`, `Cart __init__`, `Cart Context Processor`, `Cart __len__`, `Cart Pricing & Checkout Integration`, `Cart Forms & Views`, `Product Model & Favorites`, `Order Lifecycle Views`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `CustomUser` (e.g. with `CustomAccountAdapter` and `CustomSocialAccountAdapter`) actually correct?**
  _`CustomUser` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `Decimal` (e.g. with `.setUp()` and `.test_get_discount()`) actually correct?**
  _`Decimal` has 30 INFERRED edges - model-reasoned connections that need verification._