import datetime
import pytest
import server
from flask import url_for
from webhook_sender import CFG, ses, eng, models, sender

MULTIPLIER = int(CFG.get('webhook', 'MULTIPLIER'))
RETRIES = int(CFG.get('webhook', 'RETRIES'))


@pytest.mark.usefixtures('live_server')
class TestLiveServer:

    def test_send(self):
        url = url_for('wh', _external=True)
        hook = models.Webhook(url=url, message="hello")
        sender.send_webhook(hook)
        assert hook.received

    def test_send_bad(self):
        url = url_for('wh', _external=True)
        hook = models.Webhook(url=url, message="badmessage")
        sender.send_webhook(hook)
        assert not hook.received
        assert hook.retryat > datetime.datetime.utcnow()
        assert hook.attempts == 1

    def test_max_retries(self):
        url = url_for('wh', _external=True)
        hook = models.Webhook(url=url, message="badmessage")
        for i in range(0, RETRIES + 1):
            sender.send_webhook(hook, commit=True)
            assert not hook.received
            hook.retryat = datetime.datetime.utcnow()
        
        hooks = ses.query(models.Webhook).filter(models.Webhook.received==False,
                                         models.Webhook.retryat<=datetime.datetime.utcnow(),
                                         models.Webhook.attempts<=RETRIES,
                                         models.Webhook.id==hook.id)
        assert hooks.count() == 0
        ses.query(models.Webhook).delete()
        ses.commit()

    def test_send_all(self):
        url = url_for('wh', _external=True)
        hook = models.Webhook(url=url, message="hello")
        ses.add(hook)
        hook2 = models.Webhook(url=url, message="hello2")
        ses.add(hook2)
        try:
            ses.commit()
        except Exception as e:
            logger.exception(e)
            ses.rollback()
            ses.flush()
        resp = sender.send_all()
        assert resp
        hooks = ses.query(models.Webhook).filter(models.Webhook.received==False,
                          models.Webhook.attempts<=RETRIES)
        assert hooks.count() == 0

    def test_send_all_bad(self):
        url = url_for('wh', _external=True)
        hook = models.Webhook(url=url, message="badmessage")
        ses.add(hook)
        hook2 = models.Webhook(url=url, message="badmessage")
        ses.add(hook2)
        try:
            ses.commit()
        except Exception as e:
            logger.exception(e)
            ses.rollback()
            ses.flush()
        resp = sender.send_all()
        assert not resp
        hooks = ses.query(models.Webhook).filter(models.Webhook.received==False,
                          models.Webhook.attempts<=RETRIES)
        assert hooks.count() == 2
        ses.query(models.Webhook).delete()
        ses.commit()

    def tearDown(self):
        ses.query(models.Webhook).delete()
        ses.commit()

