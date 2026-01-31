
class Header:
    def __init__(self,
                 current_host: str = None,
                 user_email: str = None,
                 jwt_token: str = None,
                 jsessionid: str = None,
                 organization_id: int = None,
                 codparc: int = None,
                 iam_user_id: int = None,
                 gateway_token: str = None):
        self.current_host = current_host
        self.user_email = user_email
        self.jwt_token = jwt_token
        self.jsessionid = jsessionid
        self.organization_id = organization_id
        self.codparc = codparc
        self.iam_user_id = iam_user_id
        self.gateway_token = gateway_token