Quick hack to dump a moin wiki to static HTML with attachments.

You may need to turn of surge protection with::
    
    surge_action_limits = None # disable surge protection

in ``wikiconfig.py``.

Does not fetch scripts.  Does not fetch images referenced from CSS.

Runs in Python 2.7 and 3
