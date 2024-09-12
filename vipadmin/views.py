
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny

from rest_framework.decorators import api_view,permission_classes,throttle_classes



from vipadmin.schema import schema,AnnonySchema # Import your GraphQL schema

from graphene_file_upload.django import FileUploadGraphQLView

#GH5PJ6jAW9N.#mZ


@csrf_exempt
@api_view(["GET","POST"])
@permission_classes([AllowAny])
def graphql_token_view(request):
    print(request.body)
    # print(request)
    # print(request.data)
     #this line is very important he solve mis understand error but he solve is
    if request.user.is_authenticated:
        return FileUploadGraphQLView.as_view(graphiql=True, schema=schema)(request)
    else:
        print('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwccccccccccccc')
        return FileUploadGraphQLView.as_view(graphiql=True, schema=AnnonySchema)(request)
