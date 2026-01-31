# the data come from https://www.inpi.fr/sites/default/files/Dictionnaire_de_donnees_INPI_2024_11_06_0.xlsx (from this page: https://data.inpi.fr/content/editorial/Acces_API_Entreprises)
# if you find that this file is outdated, please open an issue

LEGAL_STATUS = {
    "0001": {
        "full_name": "Fonds communs de placement, fonds commun de placement à risques, fonds professionnel de capital investissement, fonds commun de placement d’entreprise, fonds commun de titrisation et fonds de financement spécialisé",
        "acronym": "",
    },
    "1000": {"full_name": "Entrepreneur individuel", "acronym": "EI"},
    "2110": {"full_name": "Indivision entre personnes physiques", "acronym": "IPP"},
    "2120": {"full_name": "Indivision avec personne morale", "acronym": "IPM"},
    "2210": {
        "full_name": "Société créée de fait entre personnes physiques",
        "acronym": "",
    },
    "2220": {"full_name": "Société créée de fait avec personne morale", "acronym": ""},
    "2310": {
        "full_name": "Société en participation entre personnes physiques",
        "acronym": "SEP",
    },
    "2320": {
        "full_name": "Société en participation avec personne morale",
        "acronym": "SEP",
    },
    "2385": {
        "full_name": "Société en participation de professions libérales",
        "acronym": "SEP",
    },
    "2400": {"full_name": "Fiducie", "acronym": ""},
    "2700": {"full_name": "Paroisse hors zone concordataire", "acronym": ""},
    "2800": {"full_name": "Assujetti unique à la TVA", "acronym": ""},
    "2900": {
        "full_name": "Autre groupement de droit privé non doté de la personnalité morale",
        "acronym": "",
    },
    "3110": {
        "full_name": "Représentation ou agence commerciale d'état ou organisme public étranger immatriculé au RCS",
        "acronym": "",
    },
    "3120": {
        "full_name": "Société commerciale étrangère immatriculée au RCS",
        "acronym": "",
    },
    "3205": {"full_name": "Organisation internationale", "acronym": ""},
    "3210": {
        "full_name": "État, collectivité ou établissement public étranger",
        "acronym": "",
    },
    "3220": {"full_name": "Société étrangère non immatriculée au RCS", "acronym": ""},
    "3290": {
        "full_name": "Personne morale de droit étranger (autre que société étrangère) non immatriculée au registre du commerce et des sociétés",
        "acronym": "",
    },
    "4110": {
        "full_name": "Établissement public national à caractère industriel ou commercial doté d'un comptable public",
        "acronym": "",
    },
    "4120": {
        "full_name": "Établissement public national à caractère industriel ou commercial non doté d'un comptable public",
        "acronym": "",
    },
    "4130": {"full_name": "Exploitant public", "acronym": ""},
    "4140": {
        "full_name": "Établissement public local à caractère industriel ou commercial",
        "acronym": "",
    },
    "4150": {
        "full_name": "Régie d'une collectivité locale à caractère industriel ou commercial",
        "acronym": "",
    },
    "4160": {"full_name": "Institution Banque de France", "acronym": ""},
    "5191": {"full_name": "Société de caution mutuelle", "acronym": ""},
    "5192": {"full_name": "Société coopérative de banque populaire", "acronym": ""},
    "5193": {"full_name": "Caisse de crédit maritime mutuel", "acronym": ""},
    "5194": {"full_name": "Caisse (fédérale) de crédit mutuel", "acronym": ""},
    "5195": {
        "full_name": "Association coopérative inscrite (droit local Alsace Moselle)",
        "acronym": "",
    },
    "5196": {
        "full_name": "Caisse d'épargne et de prévoyance à forme coopérative",
        "acronym": "",
    },
    "5202": {"full_name": "Société en nom collectif", "acronym": "SNC"},
    "5203": {"full_name": "Société en nom collectif coopérative", "acronym": "SNC"},
    "5305": {
        "full_name": "Société d'intérêt collectif agricole en commandite par actions",
        "acronym": "SICA",
    },
    "5306": {"full_name": "Société en commandite simple", "acronym": "SCS"},
    "5307": {"full_name": "Société en commandite simple coopérative", "acronym": ""},
    "5308": {"full_name": "Société en commandite par actions", "acronym": "SCA"},
    "5309": {
        "full_name": "Société en commandite par actions coopérative",
        "acronym": "",
    },
    "5310": {"full_name": "Société en libre partenariat", "acronym": "SLP"},
    "5311": {
        "full_name": "Société d'expertise comptable en commandite par actions",
        "acronym": "",
    },
    "5312": {
        "full_name": "Société de participations d'expertise comptable en commandite par actions",
        "acronym": "",
    },
    "5313": {
        "full_name": "Société pluri-professionnelle d'exercice en commandite par actions",
        "acronym": "",
    },
    "5314": {"full_name": "Autre forme de société en commandite simple", "acronym": ""},
    "5315": {
        "full_name": "Autre forme de société en commandite par actions",
        "acronym": "",
    },
    "5370": {
        "full_name": "Société de Participations Financières de Profession Libérale Société en commandite par actions (SPFPL SCA)",
        "acronym": "",
    },
    "5385": {
        "full_name": "Société d'exercice libéral en commandite par actions",
        "acronym": "SELCA",
    },
    "5410": {"full_name": "Société nationale à responsabilité limitée", "acronym": ""},
    "5410u": {
        "full_name": "Société nationale à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5415": {
        "full_name": "Société d'économie mixte à responsabilité limitée",
        "acronym": "",
    },
    "5415u": {
        "full_name": "Société d'économie mixte à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5420": {"full_name": "Autre société à responsabilité limitée", "acronym": ""},
    "5420u": {
        "full_name": "Autre société à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5421": {
        "full_name": "Entreprise unipersonnelle sportive à responsabilité limitée",
        "acronym": "",
    },
    "5422": {
        "full_name": "Société immobilière pour le commerce et l'industrie à responsabilité limitée",
        "acronym": "SICOMI",
    },
    "5422u": {
        "full_name": "Société immobilière pour le commerce et l'industrie à responsabilité limitée à associé unique",
        "acronym": "SICOMI",
    },
    "5426": {
        "full_name": "Société immobilière de gestion à responsabilité limitée",
        "acronym": "",
    },
    "5426u": {
        "full_name": "Société immobilière de gestion à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5430": {
        "full_name": "Société d'aménagement foncier et d'équipement rural à responsabilité limitée",
        "acronym": "SAFER",
    },
    "5430u": {
        "full_name": "Société d'aménagement foncier et d'équipement rural à responsabilité limitée à associé unique",
        "acronym": "SAFER",
    },
    "5431": {
        "full_name": "Société mixte d'intérêt agricole à responsabilité limitée",
        "acronym": "SMIA",
    },
    "5431u": {
        "full_name": "Société mixte d'intérêt agricole à responsabilité limitéeà associé unique",
        "acronym": "SMIA",
    },
    "5432": {
        "full_name": "Société d'intérêt collectif agricole à responsabilité limitée",
        "acronym": "SICA",
    },
    "5438": {
        "full_name": "Société coopérative de commerçants détaillants à responsabilité limitée",
        "acronym": "",
    },
    "5439": {
        "full_name": "Société coopérative de production à responsabilité limitée",
        "acronym": "SCOP",
    },
    "5442": {
        "full_name": "Société d'attribution à responsabilité limitée",
        "acronym": "",
    },
    "5442u": {
        "full_name": "Société d'attribution à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5443": {
        "full_name": "Société coopérative de construction à responsabilité limitée",
        "acronym": "",
    },
    "5450": {
        "full_name": "Société coopérative d'attribution d'immeuble en jouissance à temps partagé à responsabilité limitée",
        "acronym": "",
    },
    "5451": {
        "full_name": "Société coopérative de consommation à responsabilité limitée",
        "acronym": "",
    },
    "5453": {
        "full_name": "Société coopérative artisanale à responsabilité limitée",
        "acronym": "",
    },
    "5454": {
        "full_name": "Société coopérative d'intérêt maritime à responsabilité limitée",
        "acronym": "",
    },
    "5455": {
        "full_name": "Société coopérative de transport routier à responsabilité limitée",
        "acronym": "",
    },
    "5456": {
        "full_name": "Société coopérative maritime à responsabilité limitée",
        "acronym": "",
    },
    "5457": {
        "full_name": "Société coopérative d'entreprises de transport routier à responsabilité limitée",
        "acronym": "",
    },
    "5458": {
        "full_name": "Société coopérative ouvrière de production à responsabilité limitée",
        "acronym": "SCOP",
    },
    "5459": {
        "full_name": "Union de sociétés coopératives à responsabilité limitée",
        "acronym": "",
    },
    "5460": {"full_name": "Autre SARL coopérative", "acronym": "SARL"},
    "5461": {
        "full_name": "Société coopérative à responsabilité limitée",
        "acronym": "",
    },
    "5462": {
        "full_name": "Société coopérative d'intérêt collectif à responsabilité limitée",
        "acronym": "SCIC",
    },
    "5463": {
        "full_name": "Société coopérative d'activité et d'emploi à responsabilité limitée",
        "acronym": "",
    },
    "5464": {
        "full_name": "Union d'économie sociale - Société coopérative à responsabilité limitée",
        "acronym": "",
    },
    "5465": {
        "full_name": "Société coopérative d'habitants à responsabilité limitée",
        "acronym": "",
    },
    "5466": {
        "full_name": "Société coopérative de crédit à responsabilité limitée",
        "acronym": "",
    },
    "5467": {
        "full_name": "Société coopérative et participative à responsabilité limitée",
        "acronym": "",
    },
    "5468": {
        "full_name": "Société coopérative de travailleurs à responsabilité limitée",
        "acronym": "",
    },
    "5469": {
        "full_name": "Union de sociétés coopératives maritimes à responsabilité limitée",
        "acronym": "",
    },
    "5470": {
        "full_name": "Société de Participations Financières de Profession Libérale Société à responsabilité limitée",
        "acronym": "SPFPL SARL",
    },
    "5470u": {
        "full_name": "Société de Participations Financières de Profession Libérale Société à responsabilité limitée à associé unique",
        "acronym": "SPFPL",
    },
    "5482": {
        "full_name": "Société de participations financières de profession libérale de conseil en propriété industrielle à responsabilité limitée",
        "acronym": "",
    },
    "5482u": {
        "full_name": "Société de participations financières de profession libérale de conseil en propriété industrielle à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5483": {
        "full_name": "Société de participations financières de profession libérale de pharmacien d'officine à responsabilité limitée",
        "acronym": "",
    },
    "5483u": {
        "full_name": "Société de participations financières de profession libérale de pharmacien d'officine à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5484": {
        "full_name": "Société d'exercice libéral de pharmaciens d'officine à responsabilité limitée",
        "acronym": "",
    },
    "5484u": {
        "full_name": "Société d'exercice libéral à responsabilité limitée à associé unique de pharmaciens d'officine",
        "acronym": "SELARLU",
    },
    "5485": {
        "full_name": "Société d'exercice libéral à responsabilité limitée",
        "acronym": "SELARL",
    },
    "5485u": {
        "full_name": "Société d'exercice libéral à responsabilité limitée à associé unique",
        "acronym": "SELARLU",
    },
    "5486": {
        "full_name": "Société d'expertise comptable à responsabilité limitée",
        "acronym": "",
    },
    "5486u": {
        "full_name": "Société d'expertise comptable à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5487": {
        "full_name": "Société de participations financières de profession libérale de notaire à responsabilité limitée",
        "acronym": "",
    },
    "5487u": {
        "full_name": "Société de participations financières de profession libérale de notaire à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5488": {
        "full_name": "Société de participations financières de profession libérale de commissaire-priseur judiciaire à responsabilité limitée",
        "acronym": "",
    },
    "5488u": {
        "full_name": "Société de participations financières de profession libérale de commissaire-priseur judiciaire à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5489": {
        "full_name": "Société de participations financières de profession libérale d'avocat à responsabilité limitée",
        "acronym": "",
    },
    "5489u": {
        "full_name": "Société de participations financières de profession libérale d'avocat à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5490": {
        "full_name": "Société de participations financières de profession libérale d'huissier de justice à responsabilité limitée",
        "acronym": "",
    },
    "5490u": {
        "full_name": "Société de participations financières de profession libérale d'huissier de justice à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5491": {
        "full_name": "Société de participations financières de profession libérale de vétérinaire à responsabilité limitée",
        "acronym": "",
    },
    "5491u": {
        "full_name": "Société de participations financières de profession libérale de vétérinaire à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5492": {
        "full_name": "Société de participations financières de profession libérale d'expert-comptable à responsabilité limitée",
        "acronym": "",
    },
    "5492u": {
        "full_name": "Société de participations financières de profession libérale d'expert-comptable à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5493": {
        "full_name": "Société de participations financières de profession libérale de commissaire de justice à responsabilité limitée",
        "acronym": "",
    },
    "5493u": {
        "full_name": "Société de participations financières de profession libérale de commissaire de justice à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5494": {
        "full_name": "Société de participations d'expertise comptable à responsabilité limitée",
        "acronym": "",
    },
    "5494u": {
        "full_name": "Société de participations d'expertise comptable à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5495": {
        "full_name": "Société pluri-professionnelle d'exercice à responsabilité limitée",
        "acronym": "",
    },
    "5496": {"full_name": "Société de presse à responsabilité limitée", "acronym": ""},
    "5496u": {
        "full_name": "Société de presse à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5497": {
        "full_name": "Société d'attribution et d'autopromotion à responsabilité limitée",
        "acronym": "",
    },
    "5497u": {
        "full_name": "Société d'attribution et d'autopromotion à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5498": {
        "full_name": "Société d'attribution d'immeuble en jouissance à temps partagé à responsabilité limitée",
        "acronym": "",
    },
    "5498u": {
        "full_name": "Société d'attribution d'immeuble en jouissance à temps partagé à responsabilité limitée à associé unique",
        "acronym": "",
    },
    "5499": {
        "full_name": "Société à responsabilité limitée (sans autre indication)",
        "acronym": "SARL",
    },
    "5499u": {
        "full_name": "Société à responsabilité limitée à associé unique",
        "acronym": "SARLU ou EURL",
    },
    "5501": {
        "full_name": "Société anonyme d'expertise comptable à conseil d'administration",
        "acronym": "SA",
    },
    "5502": {
        "full_name": "Société anonyme de participations d'expertise comptable à conseil d'administration",
        "acronym": "SA",
    },
    "5503": {
        "full_name": "Société pluri-professionnelle d'exercice à forme anonyme et conseil d'administration",
        "acronym": "",
    },
    "5504": {
        "full_name": "Société anonyme d’économie mixte à opération unique à conseil d'administration",
        "acronym": "SA",
    },
    "5505": {
        "full_name": "Société anonyme à participation ouvrière à conseil d'administration",
        "acronym": "SA",
    },
    "5506": {
        "full_name": "Société anonyme d'économie mixte locale à conseil d'administration",
        "acronym": "SA",
    },
    "5507": {
        "full_name": "Société de placement à prépondérance immobilière à capital variable à forme anonyme et à conseil d'administration",
        "acronym": "SPPICAV",
    },
    "5508": {
        "full_name": "Société d’investissement à capital fixe à forme anonyme et à conseil d'aministration",
        "acronym": "SICAF",
    },
    "5509": {
        "full_name": "Société professionnelle de placement à prépondérance immobilière à capital variable à forme anonyme et à conseil d'administration",
        "acronymSPPPICAV": "",
    },
    "5510": {
        "full_name": "Société anonyme nationale à conseil d'administration",
        "acronym": "SA",
    },
    "5511": {
        "full_name": "Société d’investissement professionnelle spécialisée à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5512": {
        "full_name": "Société de capital investissement à forme anonyme et à conseil de surveillance",
        "acronym": "",
    },
    "5513": {
        "full_name": "Société d’investissement à capital variable d’actionnariat salarié à forme anonyme et à conseil d'administration",
        "acronym": "SICAVAS",
    },
    "5514": {
        "full_name": "Société de titrisation à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5515": {
        "full_name": "Société anonyme d'économie mixte à conseil d'administration",
        "acronym": "SA",
    },
    "5516": {
        "full_name": "Société de titrisation supportant des risques d'assurances à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5517": {
        "full_name": "Société de financement spécialisé à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5518": {
        "full_name": "Société anonyme de presse à conseil d'administration",
        "acronym": "SA",
    },
    "5519": {
        "full_name": "Société d’investissement à capital variable à forme anonyme et à conseil d'administration",
        "acronym": "SICAV",
    },
    "5520": {
        "full_name": "Fonds à forme sociétale à conseil d'administration",
        "acronym": "",
    },
    "5521": {
        "full_name": "Société anonyme de coordination à conseil d'administration",
        "acronym": "SA",
    },
    "5522": {
        "full_name": "Société anonyme immobilière pour le commerce et l'industrie à conseil d'administration",
        "acronym": "SICOMI",
    },
    "5523": {
        "full_name": "Société anonyme d'attribution et d'autopromotion à conseil d'administration",
        "acronym": "SA",
    },
    "5524": {
        "full_name": "Société anonyme d'attribution d'immeubles en jouissance à temps partagé à conseil d'administration",
        "acronym": "SA",
    },
    "5525": {
        "full_name": "Société anonyme immobilière d'investissement à conseil d'administration",
        "acronym": "SA",
    },
    "5526": {
        "full_name": "Société publique locale à forme anonyme et conseil d'administration",
        "acronym": "",
    },
    "5527": {
        "full_name": "Société publique locale d'aménagement à forme anonyme et conseil d'administration",
        "acronym": "",
    },
    "5528": {
        "full_name": "Société publique locale d'aménagement d'intérêt national à forme anonyme et conseil d'administration",
        "acronym": "",
    },
    "5529": {
        "full_name": "Société anonyme d'investissement pour le développement rural à conseil d'administration",
        "acronym": "SA",
    },
    "5530": {
        "full_name": "Société anonyme d'aménagement foncier et d'équipement rural à conseil d'administration",
        "acronym": "SAFER",
    },
    "5531": {
        "full_name": "Société anonyme mixte d'intérêt agricole à conseil d'administration",
        "acronym": "SMIA",
    },
    "5532": {
        "full_name": "Société anonyme d'intérêt collectif agricole à conseil d'administration",
        "acronym": "SICA",
    },
    "5533": {
        "full_name": "Société anonyme à objet sportif et à conseil d'administration",
        "acronym": "SA",
    },
    "5534": {
        "full_name": "Société anonyme sportive professionnelle et à conseil d'administration",
        "acronym": "SA",
    },
    "5535": {"full_name": "Autre SA à conseil d'administration", "acronym": ""},
    "5542": {
        "full_name": "Société anonyme d'attribution à conseil d'administration",
        "acronym": "SA",
    },
    "5543": {
        "full_name": "Société anonyme coopérative de construction à conseil d'administration",
        "acronym": "SA",
    },
    "5546": {
        "full_name": "Société anonyme d'HLM à conseil d'administration",
        "acronym": "SA",
    },
    "5547": {
        "full_name": "Société anonyme coopérative de production de HLM à conseil d'administration",
        "acronym": "SA",
    },
    "5551": {
        "full_name": "Société anonyme coopérative de consommation à conseil d'administration",
        "acronym": "SA",
    },
    "5552": {
        "full_name": "Société anonyme coopérative de commerçants-détaillants à conseil d'administration",
        "acronym": "SA",
    },
    "5553": {
        "full_name": "Société anonyme coopérative artisanale à conseil d'administration",
        "acronym": "SA",
    },
    "5554": {
        "full_name": "Société anonyme coopérative (d'intérêt) maritime à conseil d'administration",
        "acronym": "SA",
    },
    "5555": {
        "full_name": "Société anonyme coopérative de transport à conseil d'administration",
        "acronym": "SA",
    },
    "5557": {
        "full_name": "Société anonyme coopérative ouvrière de production à conseil d'administration",
        "acronym": "SA",
    },
    "5558": {
        "full_name": "Société anonyme coopérative de production à conseil d'administration",
        "acronym": "SCOP",
    },
    "5559": {
        "full_name": "Union de sociétés coopératives à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5560": {
        "full_name": "Autre société anonyme coopérative à conseil d'administration",
        "acronym": "",
    },
    "5561": {
        "full_name": "Société anonyme coopérative maritime à conseil d'administration",
        "acronym": "SA",
    },
    "5562": {
        "full_name": "Société anonyme coopérative d'entreprises de transport routier à conseil d'administration",
        "acronym": "SA",
    },
    "5563": {
        "full_name": "Union de sociétés coopératives maritimes à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5564": {
        "full_name": "Société anonyme coopérative d'intérêt collectif d'HLM à conseil d'administration",
        "acronym": "SA",
    },
    "5565": {
        "full_name": "Société anonyme coopérative d'intérêt collectif à conseil d'administration",
        "acronym": "SA",
    },
    "5566": {
        "full_name": "Société anonyme coopérative de travailleurs à conseil d'administration",
        "acronym": "SA",
    },
    "5567": {
        "full_name": "Société anonyme coopérative de banque à conseil d'administration",
        "acronym": "SA",
    },
    "5568": {
        "full_name": "Union d'économie sociale - Société coopérative à forme anonyme et conseil d'administration",
        "acronym": "",
    },
    "5569": {
        "full_name": "Société anonyme coopérative d'intérêt collectif pour l'accession à la propriété à conseil d'administration",
        "acronym": "SA",
    },
    "5570": {
        "full_name": "Société de Participations Financières de Profession Libérale Société anonyme à conseil d'administration",
        "acronym": "SFPL",
    },
    "5580": {
        "full_name": "Société anonyme coopérative d'activité et d'emploi à conseil d'administration",
        "acronym": "SA",
    },
    "5581": {
        "full_name": "Société anonyme coopérative d'entreprises à conseil d'administration",
        "acronym": "SA",
    },
    "5582": {
        "full_name": "Société anonyme coopérative et participative à conseil d'administration",
        "acronym": "SA",
    },
    "5583": {
        "full_name": "Société coopérative européenne à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5584": {
        "full_name": "Société anonyme coopérative d'habitants à conseil d'administration",
        "acronym": "SA",
    },
    "5585": {
        "full_name": "Société d'exercice libéral à forme anonyme à conseil d'administration",
        "acronym": "",
    },
    "5586": {
        "full_name": "Société anonyme coopérative de coordination à conseil d'administration",
        "acronym": "SA",
    },
    "5587": {
        "full_name": "Société anonyme coopérative d'attribution d'immeuble en jouissance à temps partagé à conseil d'administration",
        "acronym": "SA",
    },
    "5599": {
        "full_name": "Société anonyme à conseil d'administration (sans autre indication)",
        "acronym": "SA",
    },
    "5605": {
        "full_name": "Société anonyme à participation ouvrière à directoire",
        "acronym": "SA",
    },
    "5610": {"full_name": "Société anonyme nationale à directoire", "acronym": "SA"},
    "5615": {
        "full_name": "Société anonyme d'économie mixte à directoire",
        "acronym": "SA",
    },
    "5620": {"full_name": "Fonds à forme sociétale à directoire", "acronym": ""},
    "5622": {
        "full_name": "Société anonyme immobilière pour le commerce et l'industrie à directoire",
        "acronym": "SICOMI",
    },
    "5625": {
        "full_name": "Société anonyme immobilière d'investissement à directoire",
        "acronym": "SA",
    },
    "5630": {
        "full_name": "Société anonyme d'aménagement foncier et d'équipement rural à directoire",
        "acronym": "SAFER",
    },
    "5631": {
        "full_name": "Société anonyme mixte d'intérêt agricole à directoire",
        "acronym": "SMIA",
    },
    "5632": {
        "full_name": "Société anonyme d'intérêt collectif agricole à directoire",
        "acronym": "SICA",
    },
    "5638": {
        "full_name": "Société anonyme coopérative d'entreprises de transport routier à directoire",
        "acronym": "SA",
    },
    "5639": {
        "full_name": "Société anonyme coopérative d'habitants à directoire",
        "acronym": "SA",
    },
    "5640": {
        "full_name": "Société anonyme coopérative de coordination à directoire",
        "acronym": "SA",
    },
    "5641": {
        "full_name": "Société anonyme coopérative d'intérêt collectif pour l'accession à la propriété à directoire",
        "acronym": "SA",
    },
    "5642": {
        "full_name": "Société anonyme d'attribution à directoire",
        "acronym": "SA",
    },
    "5643": {
        "full_name": "Société anonyme coopérative de construction à directoire",
        "acronym": "SA",
    },
    "5645": {
        "full_name": "Société anonyme coopérative d'attribution d'immeuble en jouissance à temps partagé à directoire",
        "acronym": "SA",
    },
    "5646": {"full_name": "Société anonyme de HLM à directoire", "acronym": "SA"},
    "5647": {
        "full_name": "Société anonyme coopérative de production de HLM à directoire",
        "acronym": "SA",
    },
    "5649": {
        "full_name": "Société anonyme coopérative maritime à directoire",
        "acronym": "SA",
    },
    "5651": {
        "full_name": "Société anonyme coopérative de consommation à directoire",
        "acronym": "SA",
    },
    "5652": {
        "full_name": "Société anonyme coopérative de commerçants-détaillants à directoire",
        "acronym": "SA",
    },
    "5653": {
        "full_name": "Société anonyme coopérative artisanale à directoire",
        "acronym": "SA",
    },
    "5654": {
        "full_name": "Société anonyme coopérative d'intérêt maritime à directoire",
        "acronym": "SA",
    },
    "5655": {
        "full_name": "Société anonyme coopérative de transport à directoire",
        "acronym": "SA",
    },
    "5656": {
        "full_name": "Union de sociétés coopératives maritimes à forme anonyme et à directoire",
        "acronym": "",
    },
    "5657": {
        "full_name": "Société anonyme coopérative ouvrière de production à directoire",
        "acronym": "SCOP",
    },
    "5658": {
        "full_name": "Société anonyme coopérative de production à directoire",
        "acronym": "SCOP",
    },
    "5659": {
        "full_name": "Union de sociétés coopératives à forme anonyme et à conseil d'administration",
        "acronym": "",
    },
    "5660": {
        "full_name": "Autre société anonyme coopérative à directoire",
        "acronym": "",
    },
    "5661": {"full_name": "Société anonyme coopérative à directoire", "acronym": "SA"},
    "5662": {
        "full_name": "Société anonyme coopérative d'intérêt collectif à directoire",
        "acronym": "SCIC",
    },
    "5663": {
        "full_name": "Société anonyme coopérative de banque à directoire",
        "acronym": "SA",
    },
    "5664": {
        "full_name": "Union d'économie sociale - Société coopérative à forme anonyme et directoire",
        "acronym": "",
    },
    "5665": {
        "full_name": "Société anonyme coopérative d'intérêt collectif d'HLM à directoire",
        "acronym": "SA",
    },
    "5666": {
        "full_name": "Société anonyme coopérative de travailleurs à directoire",
        "acronym": "SA",
    },
    "5667": {
        "full_name": "Société anonyme coopérative d'entreprises à directoire",
        "acronym": "SA",
    },
    "5668": {
        "full_name": "Société anonyme coopérative d'activité et d'emploi à directoire",
        "acronym": "SA",
    },
    "5669": {
        "full_name": "Société anonyme coopérative et participative à directoire",
        "acronym": "SA",
    },
    "5670": {
        "full_name": "Société de Participations Financières de Profession Libérale Société anonyme à Directoire",
        "acronym": "SPFPL",
    },
    "5671": {
        "full_name": "Société coopérative européenne à forme anonyme et à directoire",
        "acronym": "",
    },
    "5672": {
        "full_name": "Société anonyme d'expertise comptable à directoire",
        "acronym": "SA",
    },
    "5673": {
        "full_name": "Société anonyme de participations d'expertise comptable à directoire",
        "acronym": "SA",
    },
    "5674": {
        "full_name": "Société pluri-professionnelle d'exercice à forme anonyme et à directoire",
        "acronym": "",
    },
    "5675": {
        "full_name": "Société anonyme d'économie mixte locale à directoire",
        "acronym": "SA",
    },
    "5676": {
        "full_name": "Société anonyme d’économie mixte à opération unique à directoire",
        "acronym": "SA",
    },
    "5677": {
        "full_name": "Société de placement à prépondérance immobilière à capital variable à forme anonyme et à directoire",
        "acronym": "SPPICAV",
    },
    "5678": {
        "full_name": "Société d’investissement à capital fixe à forme anonyme et à directoire",
        "acronym": "SICAF",
    },
    "5679": {
        "full_name": "Société professionnelle de placement à prépondérance immobilière à capital variable à forme anonyme et à directoire",
        "acronym": "SPPPICAV",
    },
    "5680": {
        "full_name": "Société d’investissement professionnelle spécialisée à forme anonyme et à directoire",
        "acronym": "",
    },
    "5681": {
        "full_name": "Société de capital investissement à forme anonyme et à directoire",
        "acronym": "",
    },
    "5682": {
        "full_name": "Société d’investissement à capital variable d’actionnariat salarié à forme anonyme et à directoire",
        "acronym": "SICAVAS",
    },
    "5683": {
        "full_name": "Société de titrisation à forme anonyme et à directoire",
        "acronym": "",
    },
    "5684": {
        "full_name": "Société de titrisation supportant des risques d'assurances à forme anonyme et à directoire",
        "acronym": "",
    },
    "5685": {
        "full_name": "Société d'exercice libéral à forme anonyme à directoire",
        "acronym": "",
    },
    "5686": {"full_name": "Société anonyme de presse à directoire", "acronym": "SA"},
    "5687": {
        "full_name": "Société anonyme de coordination à directoire",
        "acronym": "SA",
    },
    "5688": {
        "full_name": "Société anonyme d'attribution et d'autopromotion à directoire",
        "acronym": "SA",
    },
    "5689": {
        "full_name": "Société anonyme d'attribution d'immeubles en jouissance à temps partagé à directoire",
        "acronym": "SA",
    },
    "5690": {
        "full_name": "Société publique locale à forme anonyme et à directoire",
        "acronym": "",
    },
    "5691": {
        "full_name": "Société publique locale d'aménagement à forme anonyme et directoire",
        "acronym": "",
    },
    "5692": {
        "full_name": "Société publique locale d'aménagement d'intérêt national à forme anonyme et à directoire",
        "acronym": "",
    },
    "5693": {
        "full_name": "Société anonyme d'investissement pour le développement rural à directoire",
        "acronym": "SA",
    },
    "5694": {
        "full_name": "Société anonyme à objet sportif et à directoire",
        "acronym": "SA",
    },
    "5695": {
        "full_name": "Société anonyme sportive professionnelle à directoire",
        "acronym": "SA",
    },
    "5696": {"full_name": "Autre SA à directoire", "acronym": "SA"},
    "5697": {
        "full_name": "Société de financement spécialisé à forme anonyme et à directoire",
        "acronym": "",
    },
    "5698": {
        "full_name": "Société d’investissement à capital variable à forme anonyme et à directoire",
        "acronym": "SICAV",
    },
    "5699": {
        "full_name": "Société anonyme à directoire (sans autre indication)",
        "acronym": "SA",
    },
    "5701": {
        "full_name": "Société d'investissement à capital variable par actions simplifiée",
        "acronym": "SICAV",
    },
    "5702": {
        "full_name": "Société de placement à prépondérance immobilière à capital variable par actions simplifiée",
        "acronym": "SPPICAV",
    },
    "5702u": {
        "full_name": "Société d'investissement à capital variable par actions simplifiée à associé unique",
        "acronym": "SICAV",
    },
    "5703": {
        "full_name": "Société professionnelle de placement à prépondérance immobilière à capital variable par actions simplifiée",
        "acronym": "SPPPICAV",
    },
    "5703u": {
        "full_name": "Société de placement à prépondérance immobilière à capital variable par actions simplifiée à associé unique",
        "acronym": "SPPICAV",
    },
    "5704": {
        "full_name": "Société d’investissement professionnelle spécialisée par actions simplifiée",
        "acronym": "",
    },
    "5705": {
        "full_name": "Société de capital investissement par actions simplifiée",
        "acronym": "",
    },
    "5706": {
        "full_name": "Société d’investissement à capital variable d’actionnariat salarié par actions simplifiée",
        "acronym": "SICAVAS",
    },
    "5707": {
        "full_name": "Société de financement spécialisé à capital variable par actions simplifiée",
        "acronym": "",
    },
    "5707u": {
        "full_name": "Société de financement spécialisé à capital variable par actions simplifiée unipersonnelle",
        "acronym": "",
    },
    "5710": {"full_name": "Société par actions simplifiée", "acronym": "SAS"},
    "5710u": {
        "full_name": "Société par actions simplifiée unipersonnelle",
        "acronym": "SASU",
    },
    "5711": {
        "full_name": "Société d'attribution par actions simplifiée",
        "acronym": "",
    },
    "5711u": {
        "full_name": "Société d'attribution par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5712": {
        "full_name": "Société d'attribution et d'autopromotion par actions simplifiée",
        "acronym": "",
    },
    "5712u": {
        "full_name": "Société d'attribution et d'autopromotion par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5713": {
        "full_name": "Société d'attribution d'immeuble en jouissance à temps partagé par actions simplifiée",
        "acronym": "",
    },
    "5713u": {
        "full_name": "Société d'attribution d'immeuble en jouissance à temps partagé par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5714": {
        "full_name": "Société par actions simplifiée à participation ouvrière",
        "acronym": "",
    },
    "5740": {"full_name": "Société coopérative par actions simplifiée", "acronym": ""},
    "5741": {
        "full_name": "Société coopérative de production par actions simplifiée",
        "acronym": "SCOP",
    },
    "5742": {
        "full_name": "Société coopérative ouvrière de production par actions simplifiée",
        "acronym": "",
    },
    "5743": {
        "full_name": "Société coopérative d'intérêt collectif par actions simplifiée",
        "acronym": "SCIC",
    },
    "5744": {
        "full_name": "Société d'intérêt collectif agricole par actions simplifiée",
        "acronym": "SICA",
    },
    "5745": {
        "full_name": "Société coopérative d'activité et d'emploi par actions simplifiée",
        "acronym": "",
    },
    "5746": {
        "full_name": "Société coopérative et participative par actions simplifiée",
        "acronym": "",
    },
    "5747": {
        "full_name": "Union d'économie sociale - Société coopérative par actions simplifiée",
        "acronym": "",
    },
    "5748": {
        "full_name": "Union de sociétés coopératives - société par action simplifiée",
        "acronym": "",
    },
    "5749": {
        "full_name": "Société coopérative de construction par actions simplifiée",
        "acronym": "",
    },
    "5750": {
        "full_name": "Société coopérative de consommation par actions simpflifiée",
        "acronym": "",
    },
    "5751": {
        "full_name": "Société coopérative de transport routier par actions simplifiée",
        "acronym": "",
    },
    "5752": {
        "full_name": "Société coopérative d'entreprises de transport routier par actions simplifiée",
        "acronym": "",
    },
    "5753": {
        "full_name": "Société coopérative européenne par actions simplifiée",
        "acronym": "",
    },
    "5754": {
        "full_name": "Société coopérative d'habitants par actions simplifiée",
        "acronym": "",
    },
    "5755": {
        "full_name": "Société coopérative d'attribution d'immeuble en jouissance à temps partagé par actions simplifiée",
        "acronym": "",
    },
    "5756": {
        "full_name": "Société d'investissement pour le développement rural par actions simplifiée",
        "acronym": "",
    },
    "5757": {"full_name": "Autre SAS coopérative", "acronym": "SAS"},
    "5770": {
        "full_name": "Société de Participations Financières de Profession Libérale Société par actions simplifiée",
        "acronym": "SPFPL SAS",
    },
    "5770u": {
        "full_name": "Société de Participations Financières de Profession Libérale Société par actions simplifiée",
        "acronym": "SPFPLASU",
    },
    "5785": {
        "full_name": "Société d'exercice libéral par action simplifiée",
        "acronym": "SELAS",
    },
    "5785u": {
        "full_name": "Société d'exercice libéral par action simplifiée unipersonnelle",
        "acronym": "SELASU",
    },
    "5786": {
        "full_name": "Société d'exercice libéral de pharmaciens d'officine par actions simplifiée",
        "acronym": "",
    },
    "5786u": {
        "full_name": "Société d'exercice libéral de pharmaciens d'officine par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5788": {
        "full_name": "Société d'expertise comptable par actions simplifiée",
        "acronym": "",
    },
    "5788u": {
        "full_name": "Société d'expertise comptable par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5789": {
        "full_name": "Société de participations financières de profession libérale de notaire par actions simplifiée",
        "acronym": "",
    },
    "5789u": {
        "full_name": "Société de participations financières de profession libérale de notaire par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5790": {
        "full_name": "Société de participations financières de profession libérale de vétérinaire par actions simplifiée",
        "acronym": "",
    },
    "5790u": {
        "full_name": "Société de participations financières de profession libérale de vétérinaire par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5791": {
        "full_name": "Société de participations financières de profession libérale d'avocat par actions simplifiée",
        "acronym": "",
    },
    "5791u": {
        "full_name": "Société de participations financières de profession libérale d'avocat par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5792": {
        "full_name": "Société de participations financières de profession libérale de pharmacien d'officine par actions simplifiée",
        "acronym": "",
    },
    "5792u": {
        "full_name": "Société de participations financières de profession libérale de pharmacien d'officine par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5793": {
        "full_name": "Société de participations financières de profession libérale d'expert-comptable par actions simplifiée",
        "acronym": "",
    },
    "5793u": {
        "full_name": "Société de participations financières de profession libérale d'expert-comptable par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5794": {
        "full_name": "Société de participations d'expertise comptable par actions simplifiée",
        "acronym": "",
    },
    "5794u": {
        "full_name": "Société de participations d'expertise comptable par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5795": {
        "full_name": "Société pluri-professionnelle d'exercice par actions simplifiée",
        "acronym": "",
    },
    "5796": {
        "full_name": "Société mixte d'intérêt agricole par actions simplifiée",
        "acronym": "SMIA",
    },
    "5796u": {
        "full_name": "Société mixte d'intérêt agricole par actions simplifiée à associé unique",
        "acronym": "SMIA",
    },
    "5797": {
        "full_name": "Société de participations financières de profession libérale de conseil en propriété industrielle par actions simplifiée",
        "acronym": "",
    },
    "5797u": {
        "full_name": "Société de participations financières de profession libérale de conseil en propriété industrielle par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5799": {
        "full_name": "Autre forme de société par actions simplifiée",
        "acronym": "",
    },
    "5799u": {
        "full_name": "Autre forme de société par actions simplifiée à associé unique",
        "acronym": "",
    },
    "5800": {"full_name": "Société européenne", "acronym": ""},
    "6210": {
        "full_name": "Groupement européen d'intérêt économique",
        "acronym": "GEIE",
    },
    "6220": {"full_name": "Groupement d'intérêt économique", "acronym": "GIE"},
    "6316": {
        "full_name": "Coopérative d'utilisation de matériel agricole en commun",
        "acronym": "CUMA",
    },
    "6317": {"full_name": "Société coopérative agricole", "acronym": "SCA"},
    "6318": {"full_name": "Union de sociétés coopératives agricoles", "acronym": ""},
    "6399": {"full_name": "Autre société coopérative agricole", "acronym": ""},
    "6412": {"full_name": "Société d'assurances mutuelles", "acronym": ""},
    "6413": {"full_name": "Société de groupe d'assurance mutuelle", "acronym": ""},
    "6414": {"full_name": "Société de réassurance mutuelle", "acronym": ""},
    "6510": {"full_name": "Société civile d'exploitation viticole", "acronym": "SCEV"},
    "6511": {
        "full_name": "Sociétés Interprofessionnelles de Soins Ambulatoires",
        "acronym": "",
    },
    "6521": {"full_name": "Société civile de placement immobilier", "acronym": ""},
    "6531": {"full_name": "Groupement forestier d'investissement", "acronym": ""},
    "6532": {
        "full_name": "Société civile d'intérêt collectif agricole",
        "acronym": "SICA",
    },
    "6533": {
        "full_name": "Groupement agricole d'exploitation en commun",
        "acronym": "GAEC",
    },
    "6534": {"full_name": "Groupement foncier agricole", "acronym": "GFA"},
    "6535": {"full_name": "Groupement agricole foncier", "acronym": "GAF"},
    "6536": {"full_name": "Groupement forestier", "acronym": "GF"},
    "6537": {"full_name": "Groupement pastoral", "acronym": "GP"},
    "6538": {"full_name": "Groupement foncier et rural", "acronym": "GFR"},
    "6539": {"full_name": "Société civile foncière", "acronym": ""},
    "6540": {"full_name": "Société civile immobilière", "acronym": "SCI"},
    "6541": {
        "full_name": "Société civile immobilière de construction-vente",
        "acronym": "",
    },
    "6542": {"full_name": "Société civile d'attribution", "acronym": ""},
    "6543": {"full_name": "Société civile coopérative de construction", "acronym": ""},
    "6544": {
        "full_name": "Société civile immobilière d'accession progressive à la propriété",
        "acronym": "",
    },
    "6545": {
        "full_name": "Société civile d'attribution et d'autopromotion",
        "acronym": "",
    },
    "6546": {
        "full_name": "Société civile d'attribution d'immeuble en jouissance à temps partagé",
        "acronym": "",
    },
    "6547": {"full_name": "Société civile de construction-vente", "acronym": ""},
    "6550": {
        "full_name": "Union de sociétés coopératives maritimes - société civile",
        "acronym": "",
    },
    "6551": {"full_name": "Société civile coopérative de consommation", "acronym": ""},
    "6552": {"full_name": "Société civile coopérative d'habitants", "acronym": ""},
    "6553": {
        "full_name": "Société civile coopérative d'attribution d'immeuble en jouissance à temps partagé",
        "acronym": "",
    },
    "6554": {
        "full_name": "Société civile coopérative d'intérêt maritime",
        "acronym": "",
    },
    "6555": {
        "full_name": "Union de sociétés coopérative - Société civile",
        "acronym": "",
    },
    "6556": {"full_name": "Union d'économie sociale - Société civile", "acronym": ""},
    "6558": {"full_name": "Société civile coopérative entre médecins", "acronym": ""},
    "6560": {"full_name": "Autre société civile coopérative", "acronym": ""},
    "6561": {"full_name": "SCP d'avocats", "acronym": "SCP"},
    "6562": {"full_name": "SCP d'avocats aux conseils", "acronym": "SCP"},
    "6563": {"full_name": "SCP d'avoués d'appel", "acronym": "SCP"},
    "6564": {"full_name": "SCP d'huissiers", "acronym": "SCP"},
    "6565": {"full_name": "SCP de notaires", "acronym": "SCP"},
    "6566": {"full_name": "SCP de commissaire-priseur judiciaire", "acronym": "SCP"},
    "6567": {"full_name": "SCP de greffiers de tribunal de commerce", "acronym": "SCP"},
    "6568": {"full_name": "SCP de conseils juridiques", "acronym": "SCP"},
    "6569": {"full_name": "SCP de commissaires aux comptes", "acronym": "SCP"},
    "6571": {"full_name": "SCP de médecins", "acronym": "SCP"},
    "6572": {"full_name": "SCP de dentistes", "acronym": "SCP"},
    "6573": {"full_name": "SCP d'infirmiers", "acronym": "SCP"},
    "6574": {"full_name": "SCP de masseurs-kinésithérapeutes", "acronym": "SCP"},
    "6575": {
        "full_name": "SCP de directeurs de laboratoire d'analyse médicale",
        "acronym": "SCP",
    },
    "6576": {"full_name": "SCP de vétérinaires", "acronym": "SCP"},
    "6577": {"full_name": "SCP de géomètres experts", "acronym": "SCP"},
    "6578": {"full_name": "SCP d'architectes", "acronym": "SCP"},
    "6580": {"full_name": "SCP de commissaires-priseurs", "acronym": "SCP"},
    "6581": {"full_name": "SCP d'administrateurs judiciaires", "acronym": "SCP"},
    "6582": {
        "full_name": "SCP de mandataires judiciaires à la liquidation des entreprises",
        "acronym": "SCP",
    },
    "6583": {"full_name": "SCP de mandataires judiciaires", "acronym": "SCP"},
    "6584": {
        "full_name": "SCP de conseils en propriété industrielle",
        "acronym": "SCP",
    },
    "6585": {"full_name": "Autre société civile professionnelle", "acronym": "SCP"},
    "6586": {"full_name": "SCP de commissaires de justice", "acronym": "SCP"},
    "6587": {
        "full_name": "Société pluri-professionnelle d'exercice à forme civile",
        "acronym": "",
    },
    "6588": {"full_name": "Société civile de participation", "acronym": ""},
    "6589": {"full_name": "Société civile de moyens", "acronym": "SCM"},
    "6590": {"full_name": "Société civile coopérative", "acronym": ""},
    "6591": {"full_name": "Société civile de portefeuille", "acronym": ""},
    "6592": {"full_name": "Société d'épargne forestière", "acronym": ""},
    "6593": {
        "full_name": "Société civile de perception et de répartition des droits d'auteurs",
        "acronym": "",
    },
    "6594": {"full_name": "Société civile", "acronym": ""},
    "6595": {"full_name": "Caisse locale de crédit mutuel", "acronym": ""},
    "6596": {"full_name": "Caisse de crédit agricole mutuel", "acronym": ""},
    "6597": {"full_name": "Société civile d'exploitation agricole", "acronym": "SCEA"},
    "6598": {
        "full_name": "Exploitation agricole à responsabilité limitée pluripersonnelle",
        "acronym": "EARL",
    },
    "6598u": {
        "full_name": "Exploitation agricole à responsabilité limitée unipersonnelle (associé unique)",
        "acronym": "EARL",
    },  # what? why is this id the same than the previous line?
    "6599": {"full_name": "Autre société civile", "acronym": "SC"},
    "6901": {
        "full_name": "Autre personne de droit privé inscrite au registre du commerce et des sociétés",
        "acronym": "",
    },
    "7111": {"full_name": "Autorité constitutionnelle", "acronym": ""},
    "7112": {
        "full_name": "Autorité administrative ou publique indépendante",
        "acronym": "",
    },
    "7113": {"full_name": "Ministère", "acronym": ""},
    "7120": {"full_name": "Service central d'un ministère", "acronym": ""},
    "7150": {"full_name": "Service du ministère de la Défense", "acronym": ""},
    "7160": {
        "full_name": "Service déconcentré à compétence nationale d'un ministère (hors Défense)",
        "acronym": "",
    },
    "7171": {
        "full_name": "Service déconcentré de l'État à compétence (inter) régionale",
        "acronym": "",
    },
    "7172": {
        "full_name": "Service déconcentré de l'État à compétence (inter) départementale",
        "acronym": "",
    },
    "7179": {
        "full_name": "(Autre) Service déconcentré de l'État à compétence territoriale",
        "acronym": "",
    },
    "7190": {
        "full_name": "Ecole nationale non dotée de la personnalité morale",
        "acronym": "",
    },
    "7210": {"full_name": "Commune et commune nouvelle", "acronym": ""},
    "7220": {"full_name": "Département", "acronym": ""},
    "7225": {"full_name": "Collectivité et territoire d'Outre Mer", "acronym": ""},
    "7229": {"full_name": "(Autre) Collectivité territoriale", "acronym": ""},
    "7230": {"full_name": "Région", "acronym": ""},
    "7312": {"full_name": "Commune associée et commune déléguée", "acronym": ""},
    "7313": {"full_name": "Section de commune", "acronym": ""},
    "7314": {"full_name": "Ensemble urbain", "acronym": ""},
    "7321": {"full_name": "Association syndicale autorisée", "acronym": ""},
    "7322": {"full_name": "Association foncière urbaine", "acronym": ""},
    "7323": {"full_name": "Association foncière de remembrement", "acronym": ""},
    "7331": {"full_name": "Établissement public local d'enseignement", "acronym": ""},
    "7340": {"full_name": "Pôle métropolitain", "acronym": ""},
    "7341": {"full_name": "Secteur de commune", "acronym": ""},
    "7342": {"full_name": "District urbain", "acronym": ""},
    "7343": {"full_name": "Communauté urbaine", "acronym": ""},
    "7344": {"full_name": "Métropole", "acronym": ""},
    "7345": {
        "full_name": "Syndicat intercommunal à vocation multiple",
        "acronym": "SIVOM",
    },
    "7346": {"full_name": "Communauté de communes", "acronym": ""},
    "7347": {"full_name": "Communauté de villes", "acronym": ""},
    "7348": {"full_name": "Communauté d'agglomération", "acronym": ""},
    "7349": {
        "full_name": "Autre établissement public local de coopération non spécialisé ou entente",
        "acronym": "",
    },
    "7351": {"full_name": "Institution interdépartementale ou entente", "acronym": ""},
    "7352": {"full_name": "Institution interrégionale ou entente", "acronym": ""},
    "7353": {
        "full_name": "Syndicat intercommunal à vocation unique",
        "acronym": "SIVU",
    },
    "7354": {"full_name": "Syndicat mixte fermé", "acronym": ""},
    "7355": {"full_name": "Syndicat mixte ouvert", "acronym": ""},
    "7356": {
        "full_name": "Commission syndicale pour la gestion des biens indivis des communes",
        "acronym": "",
    },
    "7357": {"full_name": "Pôle d'équilibre territorial et rural", "acronym": "PETR"},
    "7361": {"full_name": "Centre communal d'action sociale", "acronym": ""},
    "7362": {"full_name": "Caisse des écoles", "acronym": ""},
    "7363": {"full_name": "Caisse de crédit municipal", "acronym": ""},
    "7364": {"full_name": "Établissement d'hospitalisation", "acronym": ""},
    "7365": {"full_name": "Syndicat inter hospitalier", "acronym": ""},
    "7366": {
        "full_name": "Établissement public local social et médico-social",
        "acronym": "",
    },
    "7367": {"full_name": "Centre Intercommunal d'action sociale", "acronym": "CIAS"},
    "7371": {
        "full_name": "Office public d'habitation à loyer modéré",
        "acronym": "OPHLM",
    },
    "7372": {
        "full_name": "Service départemental d'incendie et de secours",
        "acronym": "SDIS",
    },
    "7373": {"full_name": "Établissement public local culturel", "acronym": ""},
    "7378": {
        "full_name": "Régie d'une collectivité locale à caractère administratif",
        "acronym": "",
    },
    "7379": {
        "full_name": "(Autre) Établissement public administratif local",
        "acronym": "",
    },
    "7381": {"full_name": "Organisme consulaire", "acronym": ""},
    "7382": {
        "full_name": "Établissement public national ayant fonction d'administration centrale",
        "acronym": "",
    },
    "7383": {
        "full_name": "Établissement public national à caractère scientifique culturel et professionnel",
        "acronym": "",
    },
    "7384": {
        "full_name": "Autre établissement public national d'enseignement",
        "acronym": "",
    },
    "7385": {
        "full_name": "Autre établissement public national administratif à compétence territoriale limitée",
        "acronym": "",
    },
    "7389": {
        "full_name": "Établissement public national à caractère administratif",
        "acronym": "",
    },
    "7410": {"full_name": "Groupement d'intérêt public", "acronym": "GIP"},
    "7430": {
        "full_name": "Établissement public des cultes d'Alsace-Lorraine",
        "acronym": "",
    },
    "7450": {
        "full_name": "Etablissement public administratif, cercle et foyer dans les armées",
        "acronym": "",
    },
    "7470": {
        "full_name": "Groupement de coopération sanitaire à gestion publique",
        "acronym": "",
    },
    "7490": {
        "full_name": "Autre personne morale de droit administratif",
        "acronym": "",
    },
    "8110": {"full_name": "Régime général de la Sécurité Sociale", "acronym": ""},
    "8120": {"full_name": "Régime spécial de Sécurité Sociale", "acronym": ""},
    "8130": {"full_name": "Institution de retraite complémentaire", "acronym": ""},
    "8140": {"full_name": "Mutualité sociale agricole", "acronym": ""},
    "8150": {
        "full_name": "Régime maladie des non-salariés non agricoles",
        "acronym": "",
    },
    "8160": {
        "full_name": "Régime vieillesse ne dépendant pas du régime général de la Sécurité Sociale",
        "acronym": "",
    },
    "8170": {"full_name": "Régime d'assurance chômage", "acronym": ""},
    "8190": {"full_name": "Autre régime de prévoyance sociale", "acronym": ""},
    "8210": {"full_name": "Mutuelle", "acronym": ""},
    "8250": {"full_name": "Assurance mutuelle agricole", "acronym": ""},
    "8290": {"full_name": "Autre organisme mutualiste", "acronym": ""},
    "8310": {"full_name": "Comité social économique d’entreprise", "acronym": ""},
    "8311": {"full_name": "Comité social économique d'établissement", "acronym": ""},
    "8410": {"full_name": "Syndicat de salariés", "acronym": ""},
    "8420": {"full_name": "Syndicat patronal", "acronym": ""},
    "8450": {"full_name": "Ordre professionnel ou assimilé", "acronym": ""},
    "8470": {
        "full_name": "Centre technique industriel ou comité professionnel du développement économique",
        "acronym": "",
    },
    "8490": {"full_name": "Autre organisme professionnel", "acronym": ""},
    "8510": {"full_name": "Institution de prévoyance", "acronym": ""},
    "8520": {"full_name": "Institution de retraite supplémentaire", "acronym": ""},
    "9110": {"full_name": "Syndicat de copropriété", "acronym": ""},
    "9150": {"full_name": "Association syndicale libre", "acronym": ""},
    "9210": {"full_name": "Association non déclarée", "acronym": ""},
    "9220": {"full_name": "Association déclarée", "acronym": ""},
    "9221": {
        "full_name": "Association déclarée d'insertion par l'économique",
        "acronym": "",
    },
    "9222": {"full_name": "Association intermédiaire", "acronym": ""},
    "9223": {"full_name": "Groupement d'employeurs", "acronym": ""},
    "9224": {
        "full_name": "Association d'avocats à responsabilité professionnelle individuelle",
        "acronym": "",
    },
    "9230": {
        "full_name": "Association déclarée, reconnue d'utilité publique",
        "acronym": "",
    },
    "9240": {"full_name": "Congrégation", "acronym": ""},
    "9260": {
        "full_name": "Association de droit local (Bas-Rhin, Haut-Rhin et Moselle)",
        "acronym": "",
    },
    "9300": {"full_name": "Fondation", "acronym": "Fondation"},
    "9901": {"full_name": "Autre personne morale de droit privé", "acronym": ""},
    "9902": {"full_name": "Fonds de dotation", "acronym": ""},
    "9970": {
        "full_name": "Groupement de coopération sanitaire à gestion privée",
        "acronym": "",
    },
}


def get_legal_status_label(code):
    try:
        return LEGAL_STATUS[code]
    except KeyError:
        return "No label found for this legal status code."

def get_legal_status_acronym(code):
    try:
        return LEGAL_STATUS[code]["acronym"]
    except KeyError:
        return None


def get_legal_status_from_json(json):
    """
    Get the legal status from the JSON response.
    If the company is an associated unique company, add the "u" suffix to the code to match de deduplicated legal status code.
    """
    try:
        legal_status_code = json[0]["formality"]["formeJuridique"]
    except KeyError:
        try:
            legal_status_code = json[0]["formality"]["content"]["identité"][
                "entreprise"
            ]["formeJuridique"]
        except KeyError:
            try:
                legal_status_code = json[0]["formality"]["content"]["natureCreation"][
                    "formeJuridique"
                ]
            except KeyError:
                legal_status_code = None

    if not legal_status_code:
        return

    # If the company is an associated unique company, add the "u" suffix to the code
    if json[0]["formality"]["content"]["personneMorale"]["identite"]["description"]["indicateurAssocieUnique"]:
        legal_status_code = legal_status_code + "u"

    return {"code": legal_status_code, "label": get_legal_status_label(legal_status_code), "acronym": get_legal_status_acronym(legal_status_code)}
