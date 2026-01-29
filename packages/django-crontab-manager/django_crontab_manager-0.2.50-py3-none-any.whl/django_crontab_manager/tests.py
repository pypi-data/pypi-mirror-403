

import uuid
import json

from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Project
from .models import ServerGroup
from .models import Server
from .models import Schedule
from .models import Result
from .services import report_result

User = get_user_model()

class TestDjangoCrontabManager(TestCase):

    def setUp(self):
        self.user1 = User()
        self.user1.username = str(uuid.uuid4())
        self.user1.email = self.user1.username + "@example.com"
        self.user1.is_active = True
        self.user1.is_staff = True
        self.user1.is_superuser = True
        self.user1.save()
    
        self.sg1 = ServerGroup()
        self.sg1.name = str(uuid.uuid4())
        self.sg1.uid = str(uuid.uuid4())
        self.sg1.aclkey = str(uuid.uuid4())
        self.sg1.owner = self.user1
        self.sg1.save()

        self.server1 = str(uuid.uuid4())
        self.server2 = str(uuid.uuid4())
    
        self.scd1 = Schedule()
        self.scd1.owner = self.user1
        self.scd1.servergroup = self.sg1
        self.scd1.title = str(uuid.uuid4())
        self.scd1.save()

    def tearDown(self):
        Result.objects.all().delete()
        Server.objects.all().delete()
        Schedule.objects.all().delete()
        ServerGroup.objects.all().delete()
        Project.objects.all().delete()

    def test01(self):
        url = reverse("django_crontab_manager.get_servergroup_schedules")

        params = {
            "servergroup": self.sg1.uid,
            "aclkey": self.sg1.aclkey,
            "node": self.server1,
        }
        client = Client()
        response = client.post(url, data=params, content_type="application/json")
        response_data = json.loads(response.content)
        assert response_data["success"]
        assert self.sg1.alive_server_number() == 1
        assert len(response_data["result"]) == 1

        params = {
            "servergroup": self.sg1.uid,
            "aclkey": self.sg1.aclkey,
            "node": self.server1,
        }
        client = Client()
        response = client.post(url, data=params, content_type="application/json")
        response_data = json.loads(response.content)
        assert response_data["success"]
        assert self.sg1.alive_server_number() == 1
        assert len(response_data["result"]) == 1
        
        params = {
            "servergroup": self.sg1.uid,
            "aclkey": self.sg1.aclkey,
            "node": self.server2,
        }
        client = Client()
        response = client.post(url, data=params, content_type="application/json")
        response_data = json.loads(response.content)
        assert response_data["success"]
        assert self.sg1.alive_server_number() == 2
        assert len(response_data["result"]) == 0
    
    def test02(self):
        result = report_result(self.scd1.uid, code=0, stdout="OK", stderr="NOTHING")
        assert result

        rs = list(Result.objects.all())
        assert len(rs) == 1

        result = rs[0]
        assert result.success
        assert result.stdout() == "OK"
        assert result.stderr() == "NOTHING"

        assert not "None" in result.stdout_file.path
        assert not "None" in result.stderr_file.path

        assert "/" + str(result.pk) + "/" in result.stdout_file.path
        assert "/" + str(result.pk) + "/" in result.stderr_file.path

        if result.stdout_file:
            result.stdout_file.delete()
        
        if result.stderr_file:
            result.stderr_file.delete()

        result.delete()

    def test03(self):
        result = report_result(self.scd1.uid, code=1)
        assert result

        rs = list(Result.objects.all())
        assert len(rs) == 1

        result = rs[0]
        assert not result.success
        assert result.stdout() == ""
        assert result.stderr() == ""

        assert not result.stdout_file
        assert not result.stderr_file

        result.delete()

    def test04(self):
        info = self.scd1.info()
        text = json.dumps(info)
        assert text

    def test05(self):
        code1 = self.scd1.code

        self.scd1.title = str(uuid.uuid4())
        self.scd1.save()
        code2 = self.scd1.code
        assert code1 != code2

        self.scd1.schedule = "*/5 * * * *"
        self.scd1.save()
        code3 = self.scd1.code
        assert code3 != code2
        assert code3 != code1

        self.sg1.set_variable("servergroup_var_hello", "hello")
        self.sg1.save()
        self.scd1.script = "{servergroup_var_hello}"
        self.scd1.save()
        code4 = self.scd1.code
        assert self.scd1.get_script() == "hello"
        assert code4 != code3
        assert code4 != code2
        assert code4 != code1

        self.sg1.set_variable("servergroup_var_hello", "world")
        self.sg1.save()
        self.scd1.refresh_from_db()
        code5 = self.scd1.code
        assert self.scd1.get_script() == "world"
        assert code5 != code4
        assert code4 != code3
        assert code4 != code2
        assert code4 != code1

    def test06(self):
        self.scd1.refresh_from_db()
        code1 = self.scd1.code

        self.scd1.refresh_from_db()
        code2 = self.scd1.code
        assert code2 == code1

        self.sg1.name = str(uuid.uuid4())
        self.sg1.save()
        self.scd1.refresh_from_db()
        code3 = self.scd1.code
        assert code3 == code2

