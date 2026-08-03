import re

content = open('refs.bib').read()

ogryczak2007 = """@article{ogryczak2007,
  author  = {Ogryczak, W{\\l}odzimierz},
  title   = {Multicriteria models for fair resource allocation},
  journal = {Control and Cybernetics},
  volume  = {36},
  number  = {2},
  pages   = {303--332},
  year    = {2007}
}"""
content = re.sub(r'@article\{ogryczak2007,.*?\}', lambda m: ogryczak2007, content, flags=re.DOTALL)

henzinger2022 = """@inproceedings{henzinger2022,
  author    = {Henzinger, Monika and Kale, Satyen and Sarwate, Anand D. and others},
  title     = {Leximax Approximations and Representative Cohort Selection},
  booktitle = {3rd Symposium on Foundations of Responsible Computing (FORC 2022)},
  series    = {Leibniz International Proceedings in Informatics (LIPIcs)},
  volume    = {218},
  pages     = {1--22},
  year      = {2022},
  publisher = {Schloss Dagstuhl -- Leibniz-Zentrum f{\\"u}r Informatik}
}"""
content = re.sub(r'@article\{henzinger2022,.*?\}', lambda m: henzinger2022, content, flags=re.DOTALL)

nickel2005 = """@book{nickel2005,
  author    = {Nickel, Stefan and Puerto, Justo},
  title     = {Location Theory: A Unified Approach},
  publisher = {Springer},
  address   = {Berlin, Heidelberg},
  year      = {2005},
  doi       = {10.1007/3-540-27536-2}
}"""
content = re.sub(r'@article\{puerto2014,.*?\}', lambda m: nickel2005, content, flags=re.DOTALL)

kostreva1999 = """@article{kostreva1999,
  author  = {Kostreva, Michael M. and Ogryczak, W{\\l}odzimierz},
  title   = {Linear optimization with multiple equitable criteria},
  journal = {RAIRO - Operations Research},
  volume  = {33},
  number  = {3},
  pages   = {275--297},
  year    = {1999},
  doi     = {10.1051/ro:1999118}
}"""
content = re.sub(r'@article\{ogryczak1999,.*?\}', lambda m: kostreva1999, content, flags=re.DOTALL)

chong1976 = """@article{chong1976,
  author  = {Chong, Kong Ming},
  title   = {An induction theorem for rearrangements},
  journal = {Canadian Journal of Mathematics},
  volume  = {28},
  number  = {1},
  pages   = {154--160},
  year    = {1976},
  doi     = {10.4153/CJM-1976-018-9}
}"""
content = re.sub(r'@article\{chong2015,.*?\}', lambda m: chong1976, content, flags=re.DOTALL)

rosz_entropy = """@article{roszkowska2026entropy,
  author    = {Roszkowska, Ewa},
  title     = {Rank reversal phenomenon in multi-criteria decision-making},
  journal   = {Entropy},
  volume    = {28},
  number    = {1},
  pages     = {114},
  year      = {2026},
  publisher = {MDPI},
  doi       = {10.3390/e28010114}
}"""
# Just replace roszkowska entirely
content = re.sub(r'@article\{roszkowska2026entropy,.*?(?=\n@|\Z)', lambda m: rosz_entropy, content, flags=re.DOTALL)

# Delete philpott2013 and abernethy2024 entirely from bib
content = re.sub(r'@article\{philpott2013,.*?\}', '', content, flags=re.DOTALL)
content = re.sub(r'@article\{abernethy2024,.*?\}', '', content, flags=re.DOTALL)

open('refs.bib', 'w').write(content)
print("Updated refs.bib")
