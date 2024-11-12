# -*- coding: utf-8 -*-
"""tp4

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PQFYOdloaEhMwIAzjVuCh1A6sGI88pwM

### 1-Stocker le contenu de tous les fichiers dans un DataFrame
"""

!pip install pyspark
from pyspark.sql import SparkSession

# Créez une session Spark
spark = SparkSession.builder.appName("TP4_Spark_MLlib").getOrCreate()

"""# Étape 2 : Afficher le schéma du DataFrame"""

data_path="/content/data"
df = spark.read.option("header", "true").csv(data_path)
# Affichez le schéma du DataFrame
df.printSchema()

"""# Étape 3 : Remplir les valeurs manquantes avec 0"""

# Remplir les valeurs manquantes (NaN) par 0
df = df.na.fill(0)

# Afficher le schéma mis à jour
df.printSchema()

"""# Étape 4 : Ajouter une colonne "day_of_week"
"""

from pyspark.sql.functions import date_format, unix_timestamp

df = df.withColumn("day_of_week", date_format(unix_timestamp(df["InvoiceDate"], "yyyy-MM-dd HH:mm:ss").cast("timestamp"), "EEEE"))
df.show()

"""# Étape 5 : Diviser les données en ensemble d'apprentissage et de test"""

from pyspark.sql.functions import col
train_df = df.filter(col("InvoiceDate") < '2010-12-13')
test_df = df.filter(col("InvoiceDate") >= '2010-12-13')
# Afficher le nombre de lignes dans chaque ensemble
print("Nombre de lignes dans l'ensemble d'apprentissage :", train_df.count())
print("Nombre de lignes dans l'ensemble de test :", test_df.count())

"""# Etape 6:Créer un StringIndexer pour la colonne "day_of_week"
"""

from pyspark.ml.feature import StringIndexer
day_of_week_indexer = StringIndexer(inputCol="day_of_week", outputCol="day_of_week_encoded")
indexed_df = day_of_week_indexer.fit(df).transform(df)

# Display the resulting DataFrame with the new 'day_of_week_encoded' column
indexed_df.show()

"""# Étape 7 : Utiliser OneHotEncoder pour éviter l'ordre implicite"""

from pyspark.ml.feature import  OneHotEncoder
encoder = OneHotEncoder(inputCol="day_of_week_encoded", outputCol="day_of_week_onehot")
encoded_df = encoder.fit(indexed_df).transform(indexed_df)

# Afficher le DataFrame avec la nouvelle colonne 'day_of_week_onehot'
encoded_df.select("day_of_week", "day_of_week_encoded", "day_of_week_onehot").show(truncate=False)

"""# Étape 8 : Créer un VectorAssembler avec UnitPrice, Quantity et day_of_week_encoded"""

from pyspark.ml.feature import VectorAssembler

assembler = VectorAssembler(inputCols=["UnitPrice", "Quantity", "day_of_week_encoded"], outputCol="features")

"""# Étape 9 : Créer un pipeline"""

from pyspark.ml import Pipeline

pipeline = Pipeline(stages=[day_of_week_indexer, encoder, assembler])

"""Étape 10:transformer les données de l’ensemble d’apprentissage:Notre StringIndexer doit savoir combien de valeurs uniques il y a à indexer, comment
résoudre ce problème ?

# Etape 11:Transformer les données de l’ensemble d’apprentissage en se basant sur les étapes
## (stages) du pipeline.
"""

from pyspark.ml.feature import StringIndexer
from pyspark.ml import Pipeline

# Assuming 'day_of_week' is a column in your DataFrame
string_indexer = StringIndexer(inputCol="day_of_week", outputCol="day_of_week_indexed")

# Create a pipeline with the stages
pipeline = Pipeline(stages=[string_indexer])

# Fit the pipeline to the training data
fittedPipeline = pipeline.fit(train_df)

pipeline_model = pipeline.fit(train_df)
train_transformed = pipeline_model.transform(train_df)

"""# Étape 12 : Créer une instance de KMeans"""

from pyspark.ml.clustering import KMeans

kmeans = KMeans(k=20, featuresCol="features", predictionCol="prediction")

"""# Étape 13 : Lancer l’apprentissage de KMeans"""

from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType

# Assuming 'transformedTraining' contains your data
train_transformed = train_transformed.withColumn("Quantity", col("Quantity").cast(DoubleType()))
train_transformed= train_transformed.withColumn("UnitPrice", col("UnitPrice").cast(DoubleType()))

from pyspark.ml.feature import VectorAssembler

# Assuming 'transformedTraining' contains your data
feature_columns = ['Quantity', 'UnitPrice']  # Add other columns as needed

# Create a vector assembler
vector_assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")

# Transform the data using the vector assembler
cluster_input_data = vector_assembler.transform(train_transformed)

# Fit the KMeans model to the assembled features
model = kmeans.fit(cluster_input_data)

# Get the clustering result
clusteredData = model.transform(cluster_input_data)

# Show the result
clusteredData.show()

"""# 14. Effectuer des prédictions sur l’ensemble de test"""

#Assuming 'test_data' is your test set

# Transform the test data using the same VectorAssembler
test_df = test_df.withColumn("Quantity", col("Quantity").cast(DoubleType()))
test_df = test_df.withColumn("UnitPrice", col("UnitPrice").cast(DoubleType()))
test_cluster_input_data = vector_assembler.transform(test_df)

# Use the trained KMeans model to make predictions on the test data
test_clusteredData = model.transform(test_cluster_input_data)

# Show the result
test_clusteredData.show()

"""# 15. Calculer le coefficient de silhouette"""

from pyspark.ml.evaluation import ClusteringEvaluator

# Assuming 'test_clusteredData' contains the test set with cluster assignments
# 'prediction' column should contain the cluster assignments

# Evaluate clustering by computing Silhouette score
evaluator = ClusteringEvaluator()

silhouette_score = evaluator.evaluate(test_clusteredData)
print(f"Silhouette Score: {silhouette_score}")