// https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/3987486811597229/2090476422929802/7095385990720558/latest.html
// https://github.com/stefanobaghino/spark-twitter-stream-example
// https://github.com/saagie/example-spark-streaming-twitter
// https://www.toptal.com/apache/apache-spark-streaming-twitter
// https://github.com/logicalclocks/incubator-airflow/blob/master/airflow/contrib/example_dags/example_twitter_dag.py

import org.apache.spark._
import org.apache.spark.storage._
import org.apache.spark.streaming._
import org.apache.spark.streaming.twitter.TwitterUtils

import scala.math.Ordering

import twitter4j.auth.OAuthAuthorization
import twitter4j.conf.ConfigurationBuilder


System.setProperty("twitter4j.oauth.consumerKey", "")
System.setProperty("twitter4j.oauth.consumerSecret", "")
System.setProperty("twitter4j.oauth.accessToken", "")
System.setProperty("twitter4j.oauth.accessTokenSecret", "")
res0: String = null

// Directory to output top hashtags
val outputDirectory = "/twitter"

// Recompute the top hashtags every 1 second
val slideInterval = new Duration(1 * 1000)

// Compute the top hashtags for the last 5 seconds
val windowLength = new Duration(5 * 1000)

// Wait this many seconds before stopping the streaming job
val timeoutJobLength = 100 * 1000
outputDirectory: String = /twitter
slideInterval: org.apache.spark.streaming.Duration = 1000 ms
windowLength: org.apache.spark.streaming.Duration = 5000 ms
timeoutJobLength: Int = 100000

dbutils.fs.rm(outputDirectory, true)
res1: Boolean = false

var newContextCreated = false
var num = 0

// This is a helper class used for 
object SecondValueOrdering extends Ordering[(String, Int)] {
  def compare(a: (String, Int), b: (String, Int)) = {
    a._2 compare b._2
  }
}

// This is the function that creates the SteamingContext and sets up the Spark Streaming job.
def creatingFunc(): StreamingContext = {
  // Create a Spark Streaming Context.
  val ssc = new StreamingContext(sc, slideInterval)
  
  // Create a Twitter Stream for the input source. 
  val auth = Some(new OAuthAuthorization(new ConfigurationBuilder().build()))
  val twitterStream = TwitterUtils.createStream(ssc, auth)
  
  // Parse the tweets and gather the hashTags.
  val hashTagStream = twitterStream.map(_.getText).flatMap(_.split(" ")).filter(_.startsWith("#"))
  
  // Compute the counts of each hashtag by window.
  val windowedhashTagCountStream = hashTagStream.map((_, 1)).reduceByKeyAndWindow((x: Int, y: Int) => x + y, windowLength, slideInterval)

  // For each window, calculate the top hashtags for that time period.
  windowedhashTagCountStream.foreachRDD(hashTagCountRDD => {
    val topEndpoints = hashTagCountRDD.top(10)(SecondValueOrdering)
    dbutils.fs.put(s"${outputDirectory}/top_hashtags_${num}", topEndpoints.mkString("\n"), true)
    println(s"------ TOP HASHTAGS For window ${num}")
    println(topEndpoints.mkString("\n"))
    num = num + 1
  })
  
  newContextCreated = true
  ssc
}

newContextCreated: Boolean = false
num: Int = 0
defined module SecondValueOrdering
creatingFunc: ()org.apache.spark.streaming.StreamingContext

@transient val ssc = StreamingContext.getActiveOrCreate(creatingFunc)

ssc.start()
ssc.awaitTerminationOrTimeout(timeoutJobLength)

StreamingContext.getActive.foreach { _.stop(stopSparkContext = false) }

display(dbutils.fs.ls(outputDirectory))

dbutils.fs.head(s"${outputDirectory}/top_hashtags_3")
