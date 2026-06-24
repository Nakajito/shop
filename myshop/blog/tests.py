from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from blog.models import Category, Post, PostVideo, Tag

User = get_user_model()


class BlogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.category = Category.objects.create(name="Tech", slug="tech")
        self.tag = Tag.objects.create(name="Python", slug="python")
        self.post = Post.objects.create(
            title="Test Post",
            slug="test-post",
            body="<p>Test body content</p>",
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
        )
        self.post.tags.add(self.tag)

    def test_post_str(self):
        self.assertEqual(str(self.post), "Test Post")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Tech")

    def test_tag_str(self):
        self.assertEqual(str(self.tag), "Python")

    def test_post_get_absolute_url(self):
        self.assertEqual(
            self.post.get_absolute_url(),
            reverse("blog:post_detail", args=["test-post"]),
        )

    def test_category_get_absolute_url(self):
        self.assertEqual(
            self.category.get_absolute_url(),
            reverse("blog:post_list_by_category", args=["tech"]),
        )

    def test_tag_get_absolute_url(self):
        self.assertEqual(
            self.tag.get_absolute_url(),
            reverse("blog:post_list_by_tag", args=["python"]),
        )

    def test_post_video_get_embed_url_youtube(self):
        video = PostVideo.objects.create(
            post=self.post,
            video_type=PostVideo.VideoType.YOUTUBE,
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        self.assertEqual(
            video.get_embed_url(),
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        )

    def test_post_video_get_embed_url_youtube_short(self):
        video = PostVideo.objects.create(
            post=self.post,
            video_type=PostVideo.VideoType.YOUTUBE,
            url="https://youtu.be/dQw4w9WgXcQ",
        )
        self.assertEqual(
            video.get_embed_url(),
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        )

    def test_post_video_get_embed_url_vimeo(self):
        video = PostVideo.objects.create(
            post=self.post,
            video_type=PostVideo.VideoType.VIMEO,
            url="https://vimeo.com/123456789",
        )
        self.assertEqual(
            video.get_embed_url(),
            "https://player.vimeo.com/video/123456789",
        )

    def test_get_related_or_similar(self):
        post2 = Post.objects.create(
            title="Related Post",
            slug="related-post",
            body="Related content",
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
        )
        post2.tags.add(self.tag)

        similar = self.post.get_related_or_similar(limit=3)
        self.assertIn(post2, similar)

    def test_get_related_manual(self):
        post2 = Post.objects.create(
            title="Manual Related",
            slug="manual-related",
            body="Content",
            author=self.user,
            status=Post.Status.PUBLISHED,
        )
        self.post.related_posts.add(post2)

        related = self.post.get_related_or_similar(limit=3)
        self.assertIn(post2, related)


class BlogManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.published_post = Post.objects.create(
            title="Published",
            slug="published",
            body="Content",
            author=self.user,
            status=Post.Status.PUBLISHED,
        )
        self.draft_post = Post.objects.create(
            title="Draft",
            slug="draft",
            body="Draft content",
            author=self.user,
            status=Post.Status.DRAFT,
        )

    def test_published_manager(self):
        posts = Post.objects.published()
        self.assertIn(self.published_post, posts)
        self.assertNotIn(self.draft_post, posts)

    def test_drafts_manager(self):
        posts = Post.objects.drafts()
        self.assertIn(self.draft_post, posts)
        self.assertNotIn(self.published_post, posts)

    def test_by_author_manager(self):
        posts = Post.objects.by_author(self.user)
        self.assertEqual(posts.count(), 2)

    def test_search_manager(self):
        posts = Post.objects.search("Published")
        self.assertIn(self.published_post, posts)


class BlogPublicViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.category = Category.objects.create(name="Tech", slug="tech")
        self.tag = Tag.objects.create(name="Django", slug="django")
        self.post = Post.objects.create(
            title="Public Post",
            slug="public-post",
            body="<p>Public content</p>",
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
        )
        self.post.tags.add(self.tag)
        self.draft = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            body="Draft",
            author=self.user,
            status=Post.Status.DRAFT,
        )

    def test_post_list_status_200(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)

    def test_post_list_shows_published(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertContains(response, "PUBLIC POST")
        self.assertNotContains(response, "DRAFT POST")

    def test_post_list_by_category(self):
        response = self.client.get(
            reverse("blog:post_list_by_category", args=["tech"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PUBLIC POST")

    def test_post_list_by_tag(self):
        response = self.client.get(reverse("blog:post_list_by_tag", args=["django"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PUBLIC POST")

    def test_post_list_search(self):
        response = self.client.get(reverse("blog:post_list") + "?q=Public")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PUBLIC POST")

    def test_post_detail_published(self):
        response = self.client.get(
            reverse("blog:post_detail", args=["public-post"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Post")

    def test_post_detail_draft_returns_404(self):
        response = self.client.get(
            reverse("blog:post_detail", args=["draft-post"])
        )
        self.assertEqual(response.status_code, 404)


class BlogManagementViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staffuser", password="staffpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="regularpass123"
        )
        self.category = Category.objects.create(name="News", slug="news")
        self.post = Post.objects.create(
            title="Staff Post",
            slug="staff-post",
            body="Content",
            author=self.staff_user,
            category=self.category,
            status=Post.Status.PUBLISHED,
        )

    def test_dashboard_requires_staff(self):
        self.client.login(username="regular", password="regularpass123")
        response = self.client.get(reverse("blog:manage_dashboard"))
        self.assertNotEqual(response.status_code, 200)

    def test_dashboard_accessible_by_staff(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse("blog:manage_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_manage_post_list(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse("blog:manage_post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Post")

    def test_manage_post_create_get(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(reverse("blog:manage_post_create"))
        self.assertEqual(response.status_code, 200)

    def test_manage_post_create_post(self):
        self.client.login(username="staffuser", password="staffpass123")
        data = {
            "title": "New Post",
            "slug": "new-post",
            "body": "<p>New content</p>",
            "status": "draft",
            "images-TOTAL_FORMS": "0",
            "images-INITIAL_FORMS": "0",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "videos-TOTAL_FORMS": "0",
            "videos-INITIAL_FORMS": "0",
            "videos-MIN_NUM_FORMS": "0",
            "videos-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(reverse("blog:manage_post_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(slug="new-post").exists())

    def test_manage_post_edit_get(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(
            reverse("blog:manage_post_edit", args=[self.post.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_manage_post_delete(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.post(
            reverse("blog:manage_post_delete", args=[self.post.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_manage_post_delete_get_shows_confirmation(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.get(
            reverse("blog:manage_post_delete", args=[self.post.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Post")

    def test_ajax_create_category(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.post(
            reverse("blog:ajax_create_category"), {"name": "AJAX Category"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "AJAX Category")
        self.assertFalse(data["exists"])
        self.assertTrue(Category.objects.filter(name="AJAX Category").exists())

    def test_ajax_create_category_duplicate(self):
        self.client.login(username="staffuser", password="staffpass123")
        # Create first
        self.client.post(
            reverse("blog:ajax_create_category"), {"name": "Dup Category"}
        )
        # Try again
        response = self.client.post(
            reverse("blog:ajax_create_category"), {"name": "Dup Category"}
        )
        data = response.json()
        self.assertTrue(data["exists"])

    def test_ajax_create_category_requires_staff(self):
        self.client.login(username="regular", password="regularpass123")
        response = self.client.post(
            reverse("blog:ajax_create_category"), {"name": "No Access"}
        )
        self.assertNotEqual(response.status_code, 200)

    def test_ajax_create_tag(self):
        self.client.login(username="staffuser", password="staffpass123")
        response = self.client.post(
            reverse("blog:ajax_create_tag"), {"name": "AJAX Tag"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "AJAX Tag")
        self.assertFalse(data["exists"])
        self.assertTrue(Tag.objects.filter(name="AJAX Tag").exists())

    def test_ajax_create_tag_duplicate(self):
        self.client.login(username="staffuser", password="staffpass123")
        self.client.post(reverse("blog:ajax_create_tag"), {"name": "Dup Tag"})
        response = self.client.post(
            reverse("blog:ajax_create_tag"), {"name": "Dup Tag"}
        )
        data = response.json()
        self.assertTrue(data["exists"])

    def test_manage_post_create_auto_slug(self):
        self.client.login(username="staffuser", password="staffpass123")
        data = {
            "title": "Auto Slug Post Title",
            "body": "<p>Content</p>",
            "status": "draft",
            "images-TOTAL_FORMS": "0",
            "images-INITIAL_FORMS": "0",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "videos-TOTAL_FORMS": "0",
            "videos-INITIAL_FORMS": "0",
            "videos-MIN_NUM_FORMS": "0",
            "videos-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(reverse("blog:manage_post_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(slug="auto-slug-post-title").exists())
