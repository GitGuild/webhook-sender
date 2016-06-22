import datetime
import requests
from webhook_sender import CFG, models, logger, ses

MULTIPLIER = int(CFG.get('webhook', 'MULTIPLIER'))
RETRIES = int(CFG.get('webhook', 'RETRIES'))


def send_webhook(webhook, commit=False):
    """
    Send a single webhook.
    If successful, sent as received. Otherwise mark for retry again.

    :param Webhook webhook: the Webhook to send (sqlalchemy object)
    :param commit bool: Commit to the DB after updating?
    """
    webhook.attempts += 1
    r = None
    try:
        r = requests.post(str(webhook.url), data=str(webhook.message))
    except Exception as e:
        print e
        logger.exception(e)
    if r is not None and r.status_code == 200:
        webhook.received = True
        print "webhook to %s succeeded" % webhook.url
        logger.info("webhook to %s succeeded" % webhook.url)
    else:
        logger.info("webhook to %s send failed attempt %s" % (webhook.url, webhook.attempts))
        retryin = datetime.timedelta(seconds=MULTIPLIER ** RETRIES)
        webhook.retryat = datetime.datetime.utcnow() + retryin
    ses.add(webhook)
    if commit:
        try:
            ses.commit()
        except Exception as e:
            logger.exception(e)
            ses.rollback()
            ses.flush()

def send_all():
    """
    Send all webhooks that are ready for a retry.
    :return: True if there are more webhooks to send, otherwise False
    :rtype: bool
    """
    hooks = ses.query(models.Webhook).filter(models.Webhook.received == False,
                                             models.Webhook.retryat <= datetime.datetime.utcnow(),
                                             models.Webhook.attempts <= RETRIES)
    response = True
    if hooks.count() == 0:
        return False
    else:
        for hook in hooks:
            print hook
            send_webhook(hook)
            print hook.received
            if not hook.received:
                response = False
        try:
            ses.commit()
        except Exception as e:
            logger.exception(e)
            ses.rollback()
            ses.flush()
    return response


if __name__ == "__main__":
    more = send_all()\
