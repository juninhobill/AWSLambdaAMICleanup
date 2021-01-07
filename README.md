# AWSLambdaAMICleanup

Automated AMI and Snapshot Deletion on AWS Lambda for EC2 instances

This script will search for all instances having a tag with "Backup" or "backup" on it. As soon as we have the instances list, we loop through each instance and reference the AMIs of that instance. We check that the latest daily backup succeeded then we store every image that's reached its DeleteOn tag's date for
deletion. We then loop through the AMIs, deregister them and remove all the snapshots associated with that AMI.
