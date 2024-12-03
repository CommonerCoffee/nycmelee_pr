import sgg_utils

class start_gg(object):
    def __init__(self, key, auto_retry=True):
        self.key = key
        self.header = {"Authorization": "Bearer " + key}
        self.auto_retry = auto_retry

    def set_key_and_header(self, new_key):
        self.key = new_key
        self.header = {"Authorization": "Bearer " + new_key}

    # Sets automatic retry, a variable that says if run_query retries if too many requests
    def set_auto_retry(self, boo):
        self.auto_retry = boo

    def print_key(self):
        print(self.key)

    def print_header(self):
        print(self.header)

    def print_auto_retry(self):
        print(self.header)

    # List of sets for an event
    def tournament_show_sets(self, tournament_name, event_name, page_num):
        return sgg_utils.show_sets(tournament_name, event_name, page_num, self.header, self.auto_retry)
    
    # List of entrants for an event
    def tournament_show_entrants(self, tournament_name, event_name, page_num):
        return sgg_utils.show_entrants(tournament_name, event_name, page_num, self.header, self.auto_retry)