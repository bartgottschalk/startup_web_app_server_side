# Unit tests from the perspective of the programmer



from django.test import TestCase

from clientevent.models import Configuration as ClientEventConfiguration
from clientevent.models import Linkevent

from user.models import Ad, Adtype, Adstatus

from StartupWebApp.utilities import unittest_utilities


class UserAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Adtype.objects.create(title='Google AdWords')
        Adtype.objects.create(title='Facebook')
        Adstatus.objects.create(title='Draft')
        Adstatus.objects.create(title='Ready')
        Adstatus.objects.create(title='Running')
        Adstatus.objects.create(title='Stopped')
        Ad.objects.create(campaignid='1871718400', adgroupid='70252590136', final_url='www.startupwebapp.com/pythonabot', headline_1='Hi. My name is PythonABot', headline_2='I can help around your house', description_1='The best part is that we can communicate with each other in Python!', final_url_suffix='ad_cd=E0y04nClr68pywMIyUxn', ad_type=Adtype.objects.get(title='Google AdWords'), ad_status=Adstatus.objects.get(title='Running'), ad_cd='E0y04nClr68pywMIyUxn')

    def test_linkevent(self):

        response = self.client.get('/clientevent/linkevent?mb_cd=&pr_cd=&anonymous_id=&em_cd=&ad_cd=E0y04nClr68pywMIyUxn&url=/clientevent/linkevent?ad_cd=E0y04nClr68pywMIyUxn')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        #print(response.content.decode('utf8'))
        self.assertEqual(response.content.decode('utf8'), '"thank you"', '/clientevent/linkevent successful failed json validation')
        self.assertEqual(Linkevent.objects.count(), 1)
        new_linkevent = Linkevent.objects.first()
        self.assertIn('/clientevent/linkevent?ad_cd=E0y04nClr68pywMIyUxn', new_linkevent.url)
