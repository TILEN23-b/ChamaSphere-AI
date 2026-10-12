from django.test import TestCase

from django.urls import reverse


class LoginPageTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login to Your Account")

    def test_site_root_redirects_to_login(self):
        response = self.client.get("/")

        self.assertRedirects(response, reverse("accounts:login"))
