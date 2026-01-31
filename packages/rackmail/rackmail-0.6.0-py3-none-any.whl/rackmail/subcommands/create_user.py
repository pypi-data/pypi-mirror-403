from ..client import RackspaceClient
from ..utils.output_json import output_json
from ..utils.generate_random_string import generate_random_string
from requests import post

def create_user(args):
    rackspace_client = RackspaceClient()

    url = f"https://api.emailsrvr.com/v1/customers/{rackspace_client.customer_id}/domains/{args.domain}/rs/mailboxes/{args.email}"
    if args.password:
        password = args.password
    else:
        password = generate_random_string()

    request = post(url,headers=RackspaceClient().auth_header,json={"password":password})

    print(
        output_json(
            request.status_code,
            args.command,
            f"{args.email}@{args.domain}",
            f"Successfully created. Temporary Password: {password}" if request.status_code == 200 else request.text)
        )