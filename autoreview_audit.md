# Audit vérifiable de `autoreview.md`

Date de vérification : 2026-09-06  
Manuscrit audité : `Manuscrit/main.pdf` et ses sources LaTeX  
Statuts : **intégré**, **déjà satisfait**, **intégré avec nuance**, **rejeté**, **action auteur/externe**, **non vérifié**.

## Conclusion générale

L'autoreview identifie correctement les faiblesses les plus importantes : positionnement, élicitation de la résolution, puissance du protocole, analyse appariée, sensibilité à l'origine des cellules, ablations, limites de la formulation continue et reproductibilité. Ces éléments ont été intégrés quand ils étaient démontrables. En revanche, l'autoreview mélange parfois des exigences scientifiques et des objectifs quantitatifs arbitraires : huit figures nouvelles, un quota d'autocitations, une validation « réelle » à partir d'un jeu simulé, ou une propriété de monotonie des ensembles quand la largeur change. Ces points ne sont pas repris comme s'ils étaient vrais.

## 1. Structure proposée

| Point | Verdict | Vérification et traitement |
|---|---|---|
| Introduction : motivation, tolérances non transitives, cellules fixes | **déjà satisfait** | Présent dans `submission/introduction.tex` et `submission/method.tex`. |
| Distinguer $W_{\mathrm{cat}}$, $W_{\mathrm{exact}}$ et l'identifiant | **déjà satisfait** | Définitions et règle de tie-break explicites dans la section méthode. |
| Related work autonome | **intégré avec nuance** | Le positionnement a été renforcé et une table structurelle ajoutée. Une section numérotée séparée aurait fragmenté un article déjà long ; le contenu est dans l'introduction. |
| Représentation, probes, rétention, déception, queues, catégories | **déjà satisfait** | Définitions mathématiques et cas dégénérés explicités. |
| Section complète d'élicitation de $\delta$ | **intégré** | Nouvelle sous-section « Eliciting and auditing resolution widths ». |
| Propriétés mathématiques | **déjà satisfait / corrigé** | Existence, préordre complet, anonymat positionnel, monotonie, Pareto conditionnel, réplication et stabilité présents. La preuve Pareto a été corrigée. |
| Calcul fini et bornes incertaines | **déjà satisfait** | Algorithme fini, échantillonnage, ensembles possible/nécessaire, élimination et limites distingués. |
| Formulation polyédrique continue | **déjà satisfait / limité** | Caractérisation et comptage présents ; absence d'implémentation bout-en-bout déclarée. |
| Design expérimental élargi | **intégré** | 90 instances, 15 méthodes, 8 niveaux $p$, 8 largeurs, 500 perturbations, 10 000 poids. |
| Résultats, fournisseur, discussion, conclusion | **intégré** | Les résultats ont été recalculés ; la discussion sépare preuves, simulations et validation opérationnelle. |

Le plan en douze sections est pertinent comme liste de contrôle, mais pas comme obligation formelle. Le manuscrit conserve six sections numérotées pour éviter des sections très courtes.

## 2. Contribution en six points et « highlights »

- **Intégré.** L'introduction contient une contribution en six points défendable.
- **Vrai.** Les cellules fixes fournissent une égalité catégorielle transitive ; cela évite le défaut logique des tolérances d'indifférence pairwise non transitives.
- **Vrai.** Maximum et moyennes de queues sont placés avant les raffinements exacts.
- **Vrai.** $W_{\mathrm{cat}}$ et $W_{\mathrm{exact}}$ sont séparés.
- **Vrai sous hypothèses.** La compatibilité Pareto nécessite des probes monotones et séparantes retenues.
- **Vrai.** La réplication uniforme du multiensemble complet conserve les comparaisons ; une duplication sélective ne les conserve pas nécessairement.
- **Vrai.** L'échantillonnage et l'élimination par intervalles répondent à des questions différentes.
- **Vrai.** ReLexTail n'élimine pas l'élicitation des probes, multiplicités et largeurs.
- **Vrai.** La stabilité des catégories n'implique pas celle du point raffiné.
- **Vrai.** Un ensemble de gagnants observés par Monte Carlo n'est pas un certificat du possible complet.
- **Vrai.** La formulation continue reste théorique.

Un fichier de « highlights » séparé n'a pas été créé, car il dépend du portail éditorial ; les affirmations et contre-affirmations sont incorporées dans le texte.

## 3. Positionnement et table de capacités

- **Intégré avec nuance.** Une table compare objet principal, type d'incertitude et sortie habituelle pour modèles pondérés, leximax/LexPR, SMAA, ROR, DRO et ReLexTail.
- **Rejet partiel de la table originale.** Plusieurs coches/croix de l'autoreview étaient trop absolues : les familles Weighted Sum, OWA, CVaR, SMAA ou ROR ont de nombreuses variantes et peuvent recevoir des extensions de robustesse ou d'explication. Une table de rôles est plus véridique qu'un tableau binaire de « capacités ».
- **Intégré.** Le texte positionne ReLexTail entre priorité lexicographique stricte et tolérances par paires, sans revendiquer l'invention d'OWA, CVaR ou leximax.
- **Intégré.** Les incertitudes sur poids/préférences, bornes de normalisation et lois de probabilité sont distinguées.

## 4. Élicitation pratique de la résolution

| Recommandation | Verdict |
|---|---|
| $\delta$ n'est ni tolérance solveur, ni confiance, ni rayon d'incertitude | **intégré** |
| Interprétation en fraction de l'étendue active de la probe | **intégré** |
| Paires contrôlées et différence minimale capable de dominer les coordonnées suivantes | **intégré** |
| Conversion vers des unités physiques quand elle est univoque | **intégré avec nuance** : pour des probes agrégées, plusieurs exemples sont requis. |
| Répéter les questions, ordre inversé, test-retest | **scientifiquement pertinent, action externe** : nécessite des participants ; aucune donnée humaine n'a été fabriquée. |
| Conserver un intervalle plausible plutôt qu'un seul seuil | **intégré** |
| Ne pas choisir $\delta$ pour optimiser rétrospectivement un benchmark | **intégré** |
| Tester $0.005,0.01,0.02,0.03,0.05,0.075,0.10$ | **intégré**, avec $0.001$ en plus. |
| Origines $0,.25,.5,.75$ de la largeur | **intégré et exécuté** |
| Tableau normatif « préférer 0.02/0.05 » | **rejeté** : les cases proposées ne sont pas universelles et pourraient être lues comme une prescription sans élicitation. Le texte donne les critères de choix sans fausse règle. |

## 5. Figures 12 à 20 proposées

| Figure proposée | Verdict |
|---|---|
| 12 — courbe d'élicitation | **action externe** : requiert des jugements humains ; ne peut pas être simulée honnêtement. |
| 13 — heatmap largeur/origine | **intégré sous forme compacte** dans la Figure 12A : trois largeurs, quatre origines, graphique lisible. |
| 14 — distributions appariées | **intégré autrement** : effets appariés, IC, W/L/T, probabilité de supériorité et Wilcoxon figurent dans une table ; les IC par famille restent en figure. Une figure supplémentaire n'ajoutait pas assez. |
| 15 — carte tous $p,\delta$ | **non intégrée** : très dense (120 configurations plus comparateurs) et exploratoire ; `study.csv` contient tout le nécessaire. La figure principale montre le niveau focal. |
| 16 — coordonnées décisives | **intégré** : 64 $C_M$, 13 $C_{25}$, 6 $C_{50}$, 7 $T_{25}$. L'attribution directe à une probe singleton/moyenne/max n'est pas identifiable à partir de la seule première coordonnée du profil et n'est pas inventée. |
| 17 — ablation | **partiellement intégrée** : préfixes 1/2/4 et suppression des singletons. Les multiplicités « rééquilibrées » exigeraient un modèle de préférence défendable. |
| 18 — convergence intervalle | **déjà partiellement satisfaite** : budgets 64/256/1024 sur trois boîtes, volume et ensemble extérieur. Généraliser à de multiples instances et temps muraux reste une extension coûteuse. |
| 19 — runtime formulation continue | **bonne recommandation conditionnelle** : aucune donnée fictive n'a été ajoutée ; la figure de comptage théorique est conservée. |
| 20 — dashboard décisionnel | **partiellement satisfait** par les figures fournisseur, profil et intervalle. Un dashboard monolithique aurait dupliqué les informations. |

L'autoreview se contredit en signalant que six figures de plus allongeraient excessivement l'article puis en recommandant huit figures nouvelles. Une seule figure composite nouvelle a été ajoutée ; le total est maintenant 12.

## 6. Tables A à F

| Table | Verdict |
|---|---|
| A — matrice related work | **intégrée avec une sémantique plus prudente**. |
| B — registre d'élicitation | **action externe** : le protocole est décrit, mais une table remplie sans décideur serait fictive. |
| C — comparaison statistique | **intégrée** : table de méthodes et table de deux effets primaires. |
| D — ablations | **intégrée comme figure et CSV**, évite une table supplémentaire. |
| E — données réelles/publiques | **intégrée en texte + README + JSON** ; le jeu est explicitement simulé. |
| F — certification computationnelle | **déjà satisfaite par figure + JSON** ; les budgets, ensembles et volumes sont archivés. |

## 7. Données de comparaison et statistiques

### 7.1 Anciennes valeurs du manuscrit

Les valeurs reproduites dans l'autoreview étaient exactes pour l'ancien protocole à 30 tirages, mais ne devaient plus être utilisées après augmentation de la taille Monte Carlo. Elles ont été remplacées par le recalcul à 500 tirages :

- LexPR : 20.88 % de changements, regret de queue 0.5428 ;
- ReLexTail $\delta=.02$ : 19.30 %, regret 0.5411 ;
- différence appariée de changement : -1.584 points, IC 95 % [-3.482, 0.091] ;
- différence appariée de regret de queue : -0.00177, IC [-0.00329, -0.00065].

La première différence n'est pas clairement différente de zéro. Cette conclusion remplace toute lecture trop favorable de l'ancien 19.07 % contre 21.11 %.

### 7.2 Design requis

**Intégré exactement** : 90 instances, au moins 500 perturbations (500), huit niveaux $p$, huit $\delta$, quatre origines sur trois largeurs focales, 10 000 poids, tirages partagés entre méthodes.

### 7.3 Baselines

- **Intégrés** : LexPR, leximax, Mean-D, Tail25-D, Tail50-D, weighted sum, Chebyshev.
- **OWA** : les objectifs Tail25-D et Tail50-D sont des ordered weighted averages spécifiques ; une seconde étiquette OWA aurait été redondante.
- **Category-only** : évalué par $W_{\mathrm{cat}}$ (taille, changement, rétention), sans convertir arbitrairement un ensemble en point.
- **Achievement/reference point et outranking à seuils** : non ajoutés, car ils nécessitent des paramètres et informations de préférence supplémentaires. L'autoreview elle-même déconseille les comparaisons non équivalentes.

### 7.4 Analyse statistique

**Intégré** : différences moyenne et médiane, bootstrap apparié, probabilité de supériorité avec demi-poids des égalités, Wilcoxon, Holm sur deux critères focaux, W/L/T, stratification par géométrie. Les analyses par nombre de critères restent disponibles dans les données mais ne sont pas présentées comme tests confirmatoires. L'étude n'étant pas préenregistrée, les $p$-values restent descriptives.

## 8. Validation « réelle »

- **Minimum publication enhancement : intégré avec qualification.** UCI Energy Efficiency est public, CC BY 4.0, 768 conceptions de bâtiments simulées. Les objectifs sont surface, charge de chauffage et charge de refroidissement à minimiser. Après déduplication et Pareto, il reste quatre profils.
- **Vérité importante.** Ce jeu n'est pas une validation terrain : pas de bâtiments occupés, pas de décideur, pas d'élicitation et la surface n'est qu'un proxy de matière. Le manuscrit le dit explicitement.
- **Prospective procurement study : action externe.** Organisations, fournisseurs réels, parties prenantes, consentement, gouvernance et éventuellement éthique ne peuvent pas être produits localement. Le programme recommandé est repris dans les limites.

## 9. Références 2025–2026

Les DOI 1–16 et 18 ont été retrouvés dans les métadonnées éditeur/Crossref avec titres, auteurs et années matériellement conformes. La note `sources/bibliographic_verification_20260906.md` conserve les vérifications.

| Groupe | Verdict |
|---|---|
| Paradowski, Jangid, Patel, Gopisetty | **métadonnées vérifiées** ; seul Paradowski est cité parce qu'il soutient directement le diagnostic de robustesse. |
| Escamocher, Huber, Erwig, Więckowski, Shi, Zhao, Schwind | **métadonnées vérifiées** ; Huber, Erwig et Więckowski sont cités. Les autres ne sont pas nécessaires à une affirmation spécifique. |
| Kuhn, Blanchet, Garg, Arao, Xue | **métadonnées vérifiées** ; Kuhn est cité pour distinguer la DRO. |
| Pratiwi et al., DOI 10.17535/crorr.2026.0023 | **non vérifié définitivement** dans la passe finale ; non cité. Une erreur de résolution ou une limitation du service ne prouve pas que l'article n'existe pas. |
| Regaigui et al. | **métadonnées vérifiées**, mais le thème portfolio/metaheuristique n'est pas nécessaire au présent argument ; non cité. |

Ajouter 16 ou 18 références uniquement pour atteindre un quota serait une mauvaise pratique. Cinq références récentes sont citées là où elles modifient réellement le positionnement.

## 10. Autocitations Madani Bezoui

- **Principe de l'autoreview confirmé** : les autocitations doivent être scientifiquement justifiées, jamais ajoutées pour atteindre six.
- **Rejet du quota.** Les travaux de scheduling, portfolio, deep RL et conférences ne démontrent ni les propriétés de ReLexTail ni sa robustesse aux bornes. Les citer en série gonflerait artificiellement la bibliographie.
- Le DOI du logiciel ReLexTail déjà public est cité dans la disponibilité. Les travaux antérieurs restent dans `refs.bib` pour traçabilité, mais ne sont pas tous invoqués dans le texte.
- Les résumés de conférence ne sont pas traités comme des articles archivistiques, conformément à l'autoreview.

## 11. Identité bibliographique et ORCID

**Résolu.** Le bon identifiant canonique est `0000-0002-8342-7039`, celui du manuscrit. L'interrogation de l'API ORCID avec l'ancien `0000-0001-6930-1088` retourne le chemin canonique du nouveau record, ce qui est cohérent avec une fusion/redirection. Les pages HAL/DBLP anciennes doivent être corrigées, mais remplacer l'ORCID du papier par l'ancien serait faux.

## 12. Ajouts exacts demandés

- **Paragraphe $\delta$ : intégré**, reformulé pour correspondre exactement à la définition et au protocole exécuté.
- **Limite MILP dans l'abstract : intégrée.**
- **Outlook validation terrain : intégré dans la discussion**, sans prétendre qu'une étude humaine a été réalisée.

## 13. Corrections théoriques et techniques

| Point | Verdict |
|---|---|
| 13.1 preuve de Proposition 1 corrompue | **déjà réparée dans la version source auditée** ; la preuve de monotonie du profil est complète. |
| 13.2 Théorème Pareto | **corrigé** : la preuve invoque directement une probe retenue séparante, pas nécessairement un singleton. |
| 13.3 $\Psi(D^U)$ commun | **déjà explicite** : chaque candidat est évalué avec son vecteur supérieur commun sur la boîte. |
| 13.4 distinguer les incertitudes | **intégré** dans une table. Les incertitudes de données et d'appartenance à $A$ sont déclarées non modélisées. |
| 13.5 spécification numérique | **intégré** : plafond, snap à huit epsilons machine, tri/identifiants stables, arrondi extérieur, rationnels en certification, limites sur tolérances solveur. |

La suggestion de « monotonie/nesting lorsque $\delta$ change » est **fausse en général**. Même si des partitions scalaires sont alignées et se coarsissent, le minimum lexicographique de plusieurs coordonnées n'a pas nécessairement des ensembles optimaux emboîtés. Le manuscrit contient désormais cette mise en garde plutôt qu'un faux théorème.

## 14. Package de reproductibilité

- **Intégré fonctionnellement**, pas selon l'arborescence illustrative mot pour mot. Le ZIP contient sources LaTeX, scripts, code de bibliothèque requis, données synthétiques, directions, UCI avec licence/checksum, tableaux, résultats, figures vectorielles, manifeste SHA-256 et validation.
- **Tests ajoutés** : frontières de catégories, origine décalée, identifiants stables, sélection raffinée, ablation de préfixe, effets appariés, Holm, Pareto.
- **Déjà testés ailleurs dans le pipeline** : invariance singleton, profil rationnel, CVaR fractionnaire, containment intervalle, réplication uniforme, replay déterministe.
- **Limite transparente** : les anciens tests de `Experimental/` contiennent des attentes d'API obsolètes ; la suite dédiée au manuscrit est séparée et valide le pipeline effectivement utilisé.
- **Action externe restante** : publier cette révision exacte sous un nouveau DOI. Créer un ZIP local ne permet pas d'attribuer honnêtement un DOI immuable.

## 15. Checklist priorisée

### Priorité 1

- Preuves, table related work, élicitation, IC, flottants, limite MILP, outlook, ORCID et DOI cités : **faits**.
- Archive locale exacte : **faite** ; publication DOI : **action auteur**.

### Priorité 2

- Origines, coordonnées décisives, ablations, 500 perturbations, effets appariés, benchmark public : **faits**.
- Intervalle multi-instance : **non fait** ; la méthode actuelle est tellement lâche sur la boîte $p=.05$ (>99 % non résolu à 1 024 boîtes) qu'une vaste campagne apporterait surtout un constat de coût. Elle demeure une extension pertinente.

### Priorité 3

- Implémentation continue, comparaison énumération/optimisation, étude parties prenantes, dashboard logiciel, temps/acceptation/test-retest : **actions de recherche futures**. Les présenter comme achevés serait faux.

## 16. Cible finale

**Confirmée et intégrée.** Le manuscrit conclut que ReLexTail est un préordre complet, auditable et sensible à une résolution déclarée ; il ne revendique plus un avantage général de stabilité. Les bénéfices observés sont explicitement conditionnels aux probes, largeurs, origine de grille, population synthétique, poids d'évaluation et modèle d'incertitude.

## Artefacts probants

- `Manuscrit/submission/data/study.csv` — 10 800 résumés.
- `Manuscrit/submission/data/summary.json` — effets principaux et comparaisons.
- `Manuscrit/submission/data/grid_sensitivity.csv` — 1 080 lignes.
- `Manuscrit/submission/data/ablation.csv` — 360 lignes.
- `Manuscrit/submission/data/decisive_coordinates.csv` — 90 lignes.
- `Manuscrit/submission/data/uci_benchmark.json` — provenance, front et 44 résultats.
- `Manuscrit/submission/data/certification.json` — neuf exécutions certifiées.
- `Manuscrit/submission/data/validation.json` — contrôles automatiques finaux.
- `sources/bibliographic_verification_20260906.md` — DOI, ORCID et UCI.
