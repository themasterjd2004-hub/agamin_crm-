import sys

if 'test' in sys.argv:
    from massmail.utils import sendmassmail

    # Dummy send function to prevent real emails
    def dummy_send_massmail(*args, **kwargs):
        return None

    sendmassmail.send_massmail = dummy_send_massmail
