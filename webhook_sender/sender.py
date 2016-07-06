import sys
import datetime
import argparse

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
        print "webhook to %s failed" % webhook.url
        logger.info("webhook to %s send failed attempt %s" % (webhook.url, webhook.attempts))
        retryin = datetime.timedelta(seconds=MULTIPLIER ** RETRIES)
        webhook.retryat = datetime.datetime.utcnow() + retryin
    ses.add(webhook)
    if commit:
        try:
            ses.commit()
        except Exception as e:
            print e
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


def main(sys_args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog="webhook-sender",
                                     description="A simple program to manage"\
                                                 " the sending of webhooks"\
                                                 " registered in an SQL"\
                                                 " database.")

    parser.add_argument("command", choices=["add", "status", "cancel", "send"])
    parser.add_argument("--url", help="the URL to send the webhook to")
    parser.add_argument("--message", help="the message to send")
    parser.add_argument("--retryat",
                        help="UNIX time to retry webhook send",
                        type=datetime.datetime)
    parser.add_argument("--attempts",
                        help="number of attempts to send webhook",
                        type=int)
    parser.add_argument("--id", help="webhook's ID", type=int)
    parser.add_argument("--list", action='store_true')

    args = parser.parse_args(sys_args)

    if args.command == "add":
        url = args.url
        message = args.message
        retryat = args.retryat

        if url is None or message is None:
            parser.error("add command needs --url and --message.\n"\
                         "example: ./sender.py add --url {url}"\
                         " --message {message}")

        hook  = models.Webhook(url=url, message=message, retryat=retryat)
        ses.add(hook)
        ses.commit()
        print "Webhook has been added"

    if args.command == "cancel":
        hid = args.id

        if hid is None:
            parser.error("cancel command needs --id\n"\
                         "example: ./sender.py cancel --id {id}")

        hook = ses.query(models.Webhook).filter(models.Webhook.id==hid)
        if hook.count():
            hook.delete()
            ses.commit()
            print "Webhook with ID %d has been canceled" % hid
        else:
            print "Webhook with ID %d does not exist" % hid

    if args.command == 'status':
        if args.id:
            hid = args.id
            hook = ses.query(models.Webhook).filter(models.Webhook.id==hid)\
                .first()
            if hook is None:
                print "Hook with id %d not found" % hid
            else:
                print "Hook %d details:" % hid
                print "id=%d, url=%s, message=%s, retryat=%s, received=%r,"\
                      " attempts=%d" % (hook.id, hook.url, hook.message,
                                        hook.retryat, hook.received,
                                        hook.attempts)
        else:
            hooks = ses.query(models.Webhook)\
                .filter(models.Webhook.received==False,
                        models.Webhook.retryat<=datetime.datetime.utcnow())
            print "%d active hooks to send" % hooks.count()

            if hooks.count() and args.list is True:
                print "\nDetailed list:"
                for i, hook in enumerate(hooks.all()):
                    print "%d: id=%d, url=%s, message=%s, retryat=%s,"\
                          " received=%r, attempts=%d" % (i+1, hook.id,
                                                         hook.url,
                                                         hook.message,
                                                         hook.retryat,
                                                         hook.received,
                                                         hook.attempts)
            else:
                print "(use --list for more details)"

    # temporary behavior of "send" preliminar to issue #3
    # (https://github.com/GitGuild/webhook-sender/issues/3)
    if args.command == "send":
        hid = args.id
        if hid is None:
            send_all()
        else:
            hook = ses.query(models.Webhook).filter(models.Webhook.id==hid)
            if hook.count():
                send_webhook(hook.first(), commit=True)
            else:
                print "No webhook found with id %d" % hid
                print "Try using 'status --list' for webhook details"

if __name__ == "__main__":
    main()
