## Mini Restful Server For Cloud
# Introduction

The mini Cloud project  developed in Python and Flask with casssandar.It will work on the following aspects of Cloud applications:

1.The application provides a dynamically generated REST API.REST-based service interface.:Get,Delete,Put and Post
2.The application makes use of https://api.breezometer.com/ as an external REST service to complement its functionality
3.Use of Cassandar database for persisting information.
4.Support for Cassandra scalability, deployment in a container environment and  kubernetes based load balancing.
5.Implementing user accounts and access management by hash-based authentication
6. Get the data from external rest API then restore in cassandra. database implementation including data substantial write and delete.

# Documentation

1.Generating image:
	Dockerfile
	requirements.txt

2.Keeping https://api.breezometer.com/ API key
	config.py
	instance/config.py

3.Deployment command:
	command.txt

4.App:
	app.py

# Tests
1.List all data in database
http://IP address/
input 
username='username'
password='password'

2.Check the one specific record according to the day and time
http://IP address/23/04
get the 2019-3-23 4:00 Data

3.Check the one specific record according to the day and time
http://IP address/23/04
get the 2019-3-23 4:00 Data

4.Post one new data
http://IP address/04/04/goodcondition/12
Insert one record for 2019-03-04 04:00 ,and the category belongs to good conditon. It's pollutant number is 12

5.Delete one record 
http://IP address/d/04/04/
Delete the data of 2019-03-04 04:00.Only deleting the data which created from user

6.Modify one record's other feature.
http://IP address/p/04/04/12
Reset the pollutant of 2019-04-04 04:00 to 12.Only resetting the data from user create


