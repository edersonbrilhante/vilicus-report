import os
import gitlab
import base64
from docker_image import reference

PRIVATE_TOKEN=os.environ['PRIVATE_TOKEN']
PROJECT_ID=os.environ['PROJECT_ID']
IMAGE=os.environ['IMAGE']
FILE=os.environ['FILE']

gl = gitlab.Gitlab(url='https://gitlab.com', private_token=PRIVATE_TOKEN)
project = gl.projects.get(PROJECT_ID)

hostname, image = reference.Reference.split_docker_domain(reference.Reference.parse(IMAGE)['name'])
tag = reference.Reference.parse(IMAGE).get('tag') or 'latest'
file_path = '{}/{}/{}.json'.format(hostname, image, tag)


content = base64.b64encode(open(FILE, "rb").read()).decode("utf-8")
commit_message = 'Create {}'.format(file_path)
branch = 'main'
encoding = 'base64'
try:
    f = project.files.get(file_path=file_path, ref="main")
except gitlab.exceptions.GitlabGetError as e:
    if e.response_code == 404:
        project.files.create({'file_path': file_path,
            'branch': branch,
            'content': content,
            'author_email': 'contato@edersonbrilhante.com.br',
            'author_name': 'Ederson Brilhante',
            'encoding': encoding,
            'commit_message': commit_message})
else:
    f.content = content 
    f.save(branch=branch, commit_message=commit_message, encoding=encoding)