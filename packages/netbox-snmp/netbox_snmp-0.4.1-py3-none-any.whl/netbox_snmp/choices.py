from utilities.choices import ChoiceSet


class SNMPUserVersionChoices(ChoiceSet):
    V1 = "v1"
    V2C = "v2c"
    V3 = "v3"

    CHOICES = [(V1, "v1"), (V2C, "v2c"), (V3, "v3")]


class SNMPAuthChoices(ChoiceSet):
    SHA = "sha"
    MD5 = "md5"

    CHOICES = [(SHA, "sha"), (MD5, "md5")]


class SNMPPrivChoices(ChoiceSet):
    AES = "aes"
    DES = "des"
    CHOICES = [(AES, "aes"), (DES, "des")]


class SNMPLevelChoices(ChoiceSet):
    AUTH_PRIV = "auth-priv"
    AUTH_NO_PRIV = "auth-no-priv"
    NONE = "no-auth-no-priv"

    CHOICES = [(AUTH_PRIV, "auth-priv"), (AUTH_NO_PRIV, "auth-no-priv"), (NONE, "no-auth-no-priv")]


class SNMPOIDChoices(ChoiceSet):
    INCLUDED = "included"
    EXCLUDED = "excluded"

    CHOICES = [(INCLUDED, "included"), (EXCLUDED, "excluded")]


class SNMPNotifyChoices(ChoiceSet):
    TRAP = "trap"
    NOTIFY = "notify"

    CHOICES = [(TRAP, "trap"), (NOTIFY, "notify")]
