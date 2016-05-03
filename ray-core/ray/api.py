import webapp2, json
from endpoint import EndpointHandler
from login import LoginHandler
from actions import ActionAPI
from . import exceptions, http


def to_json(fnc):
    def inner(*args, **kwargs):
        response = args[0].response
        response.status = 200
        response.headers['Content-Type'] = 'application/json'
        from_func = fnc(*args, **kwargs)

        result = json.dumps({'result': from_func})
        return response.out.write(result)

    return inner


class ApiHandler(webapp2.RequestHandler):
    """
        This class is the beginning of all entrypoint in the Ray API. Here, each url
        will be redirect to the right handler: ActionHandler, LoginHandler or EndpointHandler.
    """

    @to_json
    def dispatch(self):
        url = self.__fix_url(self.request.path)

        try:
            return self.process(url)
        except (exceptions.ModelNotFound, exceptions.MethodNotFound, exceptions.ActionDoNotHaveModel):
            self.response.status = 404
        except (exceptions.Forbidden, exceptions.NotAuthorized):
            self.response.status = 403
        else:
            self.response.status = 500

    def process(self, fullpath):
        if self.is_login(fullpath):
            return LoginHandler(self.request, self.response, fullpath).process()

        elif self.is_endpoint(fullpath):
            return EndpointHandler(self.request, self.response, fullpath).process()

        elif self.is_action(fullpath):
            return self.__handle_action(fullpath)

        else:
            self.response.status = 404

    def __fix_url(self, url):
        if url[-1] == '/':
            return url[:-1]
        return url

    def __handle_action(self, url):
        # url e.g: /api/user/123/action

        action_url = http.param_at(url, -1)
        model_name = http.param_at(url, 2)
        model_id = http.param_at(url, 3)
        return ActionAPI(model_name).process_action(action_url, model_id)

    def is_login(self, full_path):
        return full_path == '/api/_login'

    def is_endpoint(self, full_path):
        return len(full_path.split('/')) <= 4 and len(full_path.split('/')) > 2

    def is_action(self, full_path):
        return len(full_path.split('/')) == 5
