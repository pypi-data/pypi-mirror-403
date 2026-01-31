SPARK_OPERATIONS = {
    "LivySessions": "livySessions",
    "Setting": "settings",
    "Pool": "pools",
}

ENVIRONMENT_COLLECTIONS = {
    "Library": "libraries",
    "SparkCompute": "sparkcompute",
}

LAKEHOUSE_COLLECTIONS = {
    "Table": "tables",
}


class SparkOperation:
    LivySessions = SPARK_OPERATIONS["LivySessions"]
    Setting = SPARK_OPERATIONS["Setting"]
    Pool = SPARK_OPERATIONS["Pool"]


class EnvironmentCollection:
    Library = ENVIRONMENT_COLLECTIONS["Library"]
    SparkCompute = ENVIRONMENT_COLLECTIONS["SparkCompute"]


class LakehouseCollection:
    Table = LAKEHOUSE_COLLECTIONS["Table"]
