import argparse
import ConfigParser
import logging
import requests
import service
import sqlalchemy as sa
import sqlalchemy.orm as orm
from logging.handlers import SysLogHandler
from sqlalchemy import create_engine
from webhook_sender import CFG, models, logger, eng, ses

MULTIPLIER = int(CFG.get('webhook', 'MULTIPLIER'))
RETRIES = int(CFG.get('webhook', 'RETRIES'))


class SenderService(Service):
    def __init__(self, *args, **kwargs):
        self.logger.addHandler(SysLogHandler(address=service.find_syslog(),
                                             facility=SysLogHandler.LOG_DAEMON))
        self.logger.setLevel(logging.INFO)

    def run(self):
        while not self.got_sigterm():
            try:
                more = send_all()
                if not more:
                    time.sleep(1)
            except Exception as e:
                self.logger.exception(e)

    def send_webhook(self, webhook, commit=False):
        """
        Send a single webhook.
        If successful, sent as received. Otherwise mark for retry again.

        :param Webhook webhook: the Webhook to send (sqlalchemy object)
        :param commit bool: Commit to the DB after updating?
        """
        webhook.attempts += 1
        r = requests.post(webhook.url, data=webhook.message)
        if r.status == 200:
            webhook.received = True
            self.logger.info("webhook to %s succeeded" % webhook.url)
        else:
            self.logger.info("webhook to %s send failed attempt %s with status code %s" % (webhook.url, webhook.attempts, r.status))
            retryin = datetime.timedelta(seconds=MULTIPLIER ** RETRIES)
            webhook.retryat = datetime.datetime.utcnow + retryin
        ses.add(webhook)
        if commit:
            try:
                ses.commit()
            except Exception as e:
                self.logger.exception(e)
                ses.rollback()
                ses.flush()

    def send_all(self):
        """
        Send all webhooks that are ready for a retry.
        :return: True if there are more webhooks to send, otherwise False
        :rtype: bool
        """
        hooks = ses.query(models.Webhook).filter(models.Webhook.received==False,
                                                 retryat<=datetime.datetime.utcnow)
        response = True
        if hooks.count() == 0:
            return False
        else:
            for hook in hooks:
                send_webhook(hook, False)
                if not hook.received:
                    response = False
            try:
                ses.commit()
            except Exception as e:
                self.logger.exception(e)
                ses.rollback()
                ses.flush()
        return response


def main(sys_args=sys.argv[1:]):
    service = SenderService('webhook_sender_service', pid_dir='/tmp')
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "send", "start", 
                                            "stop"])
    parser.add_argument("--url", help="the URL to send the webhook to")
    parser.add_argument("--message", help="the message to send")
    args = parser.parse_args(sys_args)
    if args.command == "start":
        service.start()
    elif args.command == "stop":
        service.stop()
    elif args.command == "send":
        hook = models.Webhook(url=args.url, message=args.message)
    elif args.command == "status":
        print "is running: %s" % service.is_running()
        hooks = ses.query(models.Webhook).filter(models.Webhook.received==False,
                                                 retryat<=datetime.datetime.utcnow).count()
        print "%s active hooks to send" % hooks


if __name__ == "__main__":
    main()
