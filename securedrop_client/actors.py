import sdclientapi
import uuid
import time

class Timer:
    def act(self, msg, tell, create):
        target = msg['target']
        target_msg = msg['target-msg']
        time.sleep(msg['sleep'])
        tell(target, target_msg)

class EventCatcher:
    def act(self, msg, tell, create):
        print("Event!", msg)
        event_key = msg[0]

        if event_key == 'password-changed':
            tell('updater', ['password', msg[1]])

        if event_key == 'username-changed':
            tell('updater', ['username', msg[1]])

        if event_key == 'tfa-changed':
            tell('updater', ['tfa', msg[1]])

        elif event_key == 'submit-clicked':
            tell('updater', ['login-submit'])

class APIClient:
    def __init__(self, api):
        self.api = api

    def act(self, msg, tell, create):
        print("API!", msg)

        req_id = msg['req_id']
        cmd = msg['cmd']
        [call_args, result, timeout] = msg['cmd-args']

        tell('api-receiver', {'req_id': req_id,
                              'action': 'newreq'})

        timed_actor = create(Timer())
        tell(timed_actor.name, {'sleep': 10,
                                'target': 'api-receiver',
                                'target-msg': {'req_id': req_id,
                                               'action': 'timeout',
                                               'action-cb': timeout}})


        fn = getattr(self.api, cmd)
        res = fn(*call_args)

        tell('api-receiver', {'req_id': req_id,
                              'action': 'result',
                              'action-cb': result,
                              'action-args': res})

        print("GOT RES", res)


class APIMultiplexer:
    def __init__(self):
        self.api = None

    def act(self, msg, tell, create):
        [cmd, args] = msg

        if cmd == "configure":
            [hostname, username, password, totp, proxy] = args
            self.api = sdclientapi.API(hostname, username,
                                       password, totp, proxy)
            # tell('nothing', {})
        else:
            req_id = str(uuid.uuid4())
            api = create(APIClient(self.api))
            tell(api.name, {'req_id': req_id,
                            'cmd': cmd,
                            'cmd-args': args})

class Receiver:
    def __init__(self):
        self.current_reqs = {}

    def act(self, msg, tell, create):
        print("Receiver", msg)
        req_id = msg['req_id']
        action = msg['action']

        if action == 'newreq':
            self.current_reqs[req_id] = True

        elif action == 'timeout' and req_id in self.current_reqs:
            print("Request timed out.")

            action_cb = msg['action-cb']
            cb_actor = action_cb[0]
            cb_args = action_cb[1:]
            tell(cb_actor, cb_args)

            del self.current_reqs[req_id]

        elif action == 'resp' and req_id in self.current_reqs:
            del self.current_reqs[req_id]

            resp = msg['resp']
            action_cb = msg['action-cb']
            cb_actor = action_cb[0]
            cb_args = action_cb[1:]
            cb_args.append(resp)
            tell(cb_actor, cb_args)

        else:
            print("Not sure what to do with {} {}".format(action, req_id))


class LoginResult:
    def act(self, msg, tell, create):
        print("Login result got", msg)

class LoginSubmitter:
    def act(self, msg, tell, create):
        [username, password, totp] = msg

        hostname = "http://localhost:8081"
        proxy = True

        tell('api-multiplexer', ['configure',
                                 [hostname, username, password, totp, proxy]])

        tell('api-multiplexer', ['authenticate',
                                 [[], # args to command (authenticate, in this case)
                                  ['login-result','result'],
                                  ['login-result','timeout']]])

# All database mutations route through this actor
class DBUpdater:
    def __init__(self, db):
        self.db = db

    def act(self, msg, tell, create):
        msg_key = msg[0]
        print("msg", msg)
        if msg_key == 'password':
            self.db.assoc_in(['login', 'new-password-text'], msg[1])

        elif msg_key == 'username':
            self.db.assoc_in(['login', 'new-user-text'], msg[1])

        elif msg_key == 'tfa':
            self.db.assoc_in(['login', 'new-tfa-text'], msg[1])

        elif msg_key == 'login-submit':
            self.db.assoc_in(['login', 'submitting'], True)

            submitter = create(LoginSubmitter())

            tell(submitter.name, [self.db.get_in(['login','new-user-text']),
                                  self.db.get_in(['login','new-password-text']),
                                  self.db.get_in(['login','new-tfa-text'])])
