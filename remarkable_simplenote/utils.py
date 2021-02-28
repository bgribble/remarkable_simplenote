
from subprocess import run, Popen, PIPE
from .conf import config

def get_pdf_title(path):
    exiftool_cmd = [
        'exiftool', '-S', '-Title', path
    ]
    output = run(exiftool_cmd, capture_output=True)
    line = output.stdout.split(b'\n')[0].decode('utf-8')
    if line:
        return line.split(" ", 1)[1]
    else:
        return path.split("/")[-1]

def write_pdf(*, title, body, destination):
    pdf_engine = config.get('pdf_engine') 
    pandoc_cmd = [
        'pandoc',
        '-f', 'markdown',
        f'--pdf-engine={pdf_engine}',
        '-o', destination,
        '-'
    ]

    with Popen(pandoc_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as p:
        p.communicate(body.encode('utf-8'))

    exiftool_cmd = [
        'exiftool',
        f'-Title={title}',
        destination,
    ]
    run(exiftool_cmd, capture_output=True)

