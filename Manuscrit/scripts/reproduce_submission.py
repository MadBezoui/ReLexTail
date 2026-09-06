"""One-command reproduction of the submission version, from repository root."""
from pathlib import Path
import subprocess,sys,os
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'submission/.mplcache'))
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
for name in ['submission_study.py','submission_extensions.py','submission_certification.py','submission_figures.py']:
    subprocess.run([sys.executable,str(HERE/name)],check=True)
subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(HERE/'validate_submission.py')],check=True)
