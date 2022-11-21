from http import HTTPStatus

from django.test import Client, TestCase


class ViewTestClass(TestCase):
    
    def setUp(self):
        
        self.anon = Client()
        self.auth = Client()
        
    
    def test_error_page(self):
        """Проверка, что используется кастомный шаблон 404"""
        response = self.auth.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "core/404.html")