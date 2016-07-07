import pytest
import random
import datetime

from webhook_sender.sender import main, ses, models

test_pin = ''.join([str(n) for n in random.sample(xrange(10), 6)])


class TestCLICommands:

    def test_add(self):
        args = 'add --url http://test.com --message ' + test_pin
        main(sys_args=args.split())
        fhooks = ses.query(models.Webhook)\
            .filter(models.Webhook.message == test_pin)

        assert fhooks.count() == 1

        hook = fhooks.first()

        assert type(hook.id) == int
        assert hook.url.encode('utf-8') == 'http://test.com'
        assert hook.message.encode('utf-8') == test_pin
        assert type(hook.retryat) == datetime.datetime
        assert type(hook.received) == bool
        assert type(hook.attempts) == int

    def test_add_without_url(self, capsys):
        test_pin_nourl = test_pin + 'nourl'
        args = 'add --message ' + test_pin_nourl

        with pytest.raises(SystemExit):
            main(sys_args=args.split())
        _, err = capsys.readouterr()

        fhooks = ses.query(models.Webhook)\
            .filter(models.Webhook.message == test_pin_nourl)

        expected_msg = 'error: add command needs --url and --message.'

        assert fhooks.count() == 0
        assert expected_msg in err.encode('utf-8')

    def test_add_without_message(self, capsys):
        test_pin_nomessage = test_pin + 'nomessage'
        args = 'add --url http://' + test_pin_nomessage + '.com'

        with pytest.raises(SystemExit):
            main(sys_args=args.split())
        _, err = capsys.readouterr()

        fhooks = ses.query(models.Webhook)\
            .filter(models.Webhook.message == test_pin_nomessage)

        expected_msg = 'error: add command needs --url and --message.'

        assert fhooks.count() == 0
        assert expected_msg in err.encode('utf-8')

    def test_add_nooptions(self, capsys):
        args = 'add'

        with pytest.raises(SystemExit):
            main(sys_args=args.split())
        _, err = capsys.readouterr()

        expected_msg = 'error: add command needs --url and --message.'

        assert expected_msg in err.encode('utf-8')

    def test_status(self, capsys):
        args = 'status'
        main(sys_args=args.split())
        out, _ = capsys.readouterr()

        expected_msg = 'active hooks to send'

        assert expected_msg in out

    def test_status_list(self, capsys):
        args = 'status --list'
        main(sys_args=args.split())
        out, _ = capsys.readouterr()

        expected_msg = 'active hooks to send'
        expected_msg2 = 'Detailed list:'

        assert expected_msg in out
        assert expected_msg2 in out

    def test_cancel(self):
        test_pin_cancel = test_pin + 'cancel'
        hook = models.Webhook(url='http://test.com', message=test_pin_cancel)
        ses.add(hook)
        ses.commit()

        fhooks = ses.query(models.Webhook)\
            .filter(models.Webhook.message == test_pin_cancel)

        assert fhooks.count() == 1

        hook = fhooks.first()
        hid = hook.id
        args = 'cancel --id ' + str(hid)
        main(sys_args=args.split())

        fhooks = ses.query(models.Webhook).filter(models.Webhook.id == hid)

        assert fhooks.count() == 0

    def test_cancel_without_id(self, capsys):
        n_hooks = len(ses.query(models.Webhook).all())

        args = 'cancel'
        with pytest.raises(SystemExit):
            main(sys_args=args.split())
        _, err = capsys.readouterr()

        n_hooks2 = len(ses.query(models.Webhook).all())
        expected_msg = 'error: cancel command needs --id\n'\
                       'example: ./sender.py cancel --id {id}'

        assert n_hooks == n_hooks2
        assert expected_msg in err.encode('utf-8')

    def test_cancel_nonexistent_id(self, capsys):
        n_hooks = len(ses.query(models.Webhook).all())

        args = 'cancel --id 99999999999999'
        main(sys_args=args.split())
        out, _ = capsys.readouterr()

        n_hooks2 = len(ses.query(models.Webhook).all())
        expected_msg = 'Webhook with ID 99999999999999 does not exist\n'

        assert n_hooks == n_hooks2
        assert expected_msg in out.encode('utf-8')

    def tearDown(self):
        ses.query(models.Webhook).delete()
        ses.commit()
