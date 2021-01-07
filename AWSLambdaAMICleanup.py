import boto3
import collections
import datetime
import sys

ec = boto3.client('ec2', 'us-east-1')
ec2 = boto3.resource('ec2', 'us-east-1')
images = ec2.images.filter(Owners=["self"])

def lambda_handler(event, context):

	reservations = ec.describe_instances(
		Filters=[
			{'Name': 'tag-key', 'Values': ['backup', 'Backup']},
		]
	).get(
		'Reservations', []
	)

	instances = sum(
		[
			[i for i in r['Instances']]
			for r in reservations
		], [])

	print("Found %d instances that need evaluated" % len(instances))

	to_tag = collections.defaultdict(list)

	date_today = datetime.datetime.now().date()

	imagesList = []
	imagesIDs = []

	# Set to true once we confirm we have a backup taken today
	backupSuccess = True

	# Loop through all of our instances with a tag named "Backup"
	for instance in instances:
		imagecount = 0
	
		# Creating variables to avoid issue with UnboundLocalError
		instance_name = ""
		delete_date = ""

		# Loop through each image of our current instance
		for image in images:

			# Our other Lambda Function names its AMIs BKP - i-instancenumber.
			# We now know these images are auto created
			if image.description.startswith('Lambda created AMI of instance ' + instance['InstanceId']):

				# Count this image's occcurance
				imagecount = imagecount + 1

				try:
					if image.tags is not None:
						deletion_date = [
							t.get('Value') for t in image.tags
							if t['Key'] == 'DeleteOn'][0]

						delete_date = datetime.datetime.strptime(deletion_date, "%m-%d-%Y").date()
						print("Delete On Date: " + str(delete_date))

						instance_name = [
							t2.get('Value') for t2 in image.tags
							if t2['Key'] == 'Name'][0]

				except IndexError:
					deletion_date = False
					delete_date = False

				today_time = datetime.datetime.now()
				today_date = today_time.date()
				print("Today Date: " + str(today_date), instance_name)

				# If image's DeleteOn date is less than or equal to today,
				# add this image to our list of images to process later
				if delete_date <= today_date and delete_date is not None:
					imagesList.append(image.name)
					imagesIDs.append(image.id)

				# Make sure we have an AMI from today and mark backupSuccess as true
				if image.name.endswith(str(date_today)):
					# Our latest backup from our other Lambda Function succeeded
					backupSuccess = True
					print("Latest backup from " + date_today + " was a success")

		print("Instance " + instance_name + " has " + str(imagecount) + " AMIs")

	print("=============")

	print("About to process the following AMIs:")
	print(imagesList)

	if backupSuccess == True:

		myAccount = boto3.client('sts').get_caller_identity()['Account']

		snapshots = ec.describe_snapshots(MaxResults=1000, OwnerIds=[myAccount])['Snapshots']

		# loop through list of image IDs
		for image in imagesIDs:
			print("deregistering image %s" % image)
			amiResponse = ec.deregister_image(
				DryRun=False,
				ImageId=image,
			)

			for snapshot in snapshots:
				if snapshot['Description'].find(image) > 0:
					snap = ec.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
					print("Deleting snapshot " + snapshot['SnapshotId'])
					print("-------------")

	else:
		print("No current backup found. Termination suspended.")

	return "Done!"
