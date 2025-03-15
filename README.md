# AWS Route 53 IP Updater

A Python script that automatically updates an AWS Route 53 DNS record with the current public IP address of the server it's running on.

## Features

- Retrieves the current public IP address from multiple reliable services
- Updates a specified Route 53 DNS record using the UPSERT action (creates or updates)
- Configurable TTL and record type
- Support for AWS profiles
- Detailed logging

## Prerequisites

- Python 3.6+
- AWS credentials configured (either via environment variables, AWS credentials file, or IAM role)
- Required permissions: Route 53 read/write access

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/seawhite/aws-r53-ip-updater.git
   cd aws-r53-ip-updater
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

```bash
python update_route53_ip.py --zone-id YOUR_HOSTED_ZONE_ID --record-name your.domain.com
```

### Required Arguments

- `--zone-id`: The AWS Route 53 Hosted Zone ID
- `--record-name`: The DNS record name to update

### Optional Arguments

- `--ttl`: Time to live in seconds (default: 300)
- `--record-type`: Record type (currently only supports 'A' records)
- `--profile`: AWS profile name to use
- `--verbose` or `-v`: Enable verbose logging

## Examples

Update a record with default settings:
```bash
python update_route53_ip.py --zone-id Z1D633PJN98FT9 --record-name home.example.com
```

Update a record with custom TTL and using a specific AWS profile:
```bash
python update_route53_ip.py --zone-id Z1D633PJN98FT9 --record-name home.example.com --ttl 60 --profile my-aws-profile
```

## Automation

### Setting Up a Cron Job

You can set up a cron job to run this script periodically. Here's how to do it:

1. Open your crontab file for editing:
   ```bash
   crontab -e
   ```

2. Add a line to run the script at your desired frequency. Some examples:

   ```bash
   # Run every hour (at minute 0)
   0 * * * * cd /path/to/aws-r53-ip-updater && /usr/bin/python3 /path/to/aws-r53-ip-updater/update_route53_ip.py --zone-id YOUR_ZONE_ID --record-name your.domain.com
   
   # Run every 15 minutes
   */15 * * * * cd /path/to/aws-r53-ip-updater && /usr/bin/python3 /path/to/aws-r53-ip-updater/update_route53_ip.py --zone-id YOUR_ZONE_ID --record-name your.domain.com
   
   # Run daily at 6 AM
   0 6 * * * cd /path/to/aws-r53-ip-updater && /usr/bin/python3 /path/to/aws-r53-ip-updater/update_route53_ip.py --zone-id YOUR_ZONE_ID --record-name your.domain.com
   ```

3. Save and exit the editor.

### Logging Cron Output

To log the output of your cron job for debugging purposes:

```bash
# Log both stdout and stderr to a file
0 * * * * cd /path/to/aws-r53-ip-updater && /usr/bin/python3 /path/to/aws-r53-ip-updater/update_route53_ip.py --zone-id YOUR_ZONE_ID --record-name your.domain.com >> /path/to/logfile.log 2>&1
```

### Running as a Systemd Service

Alternatively, you can set up a systemd service with a timer:

1. Create a service file at `/etc/systemd/system/route53-updater.service`:
   ```ini
   [Unit]
   Description=Update Route 53 DNS record with current public IP
   After=network-online.target
   Wants=network-online.target
   
   [Service]
   Type=oneshot
   ExecStart=/usr/bin/python3 /path/to/aws-r53-ip-updater/update_route53_ip.py --zone-id YOUR_ZONE_ID --record-name your.domain.com
   WorkingDirectory=/path/to/aws-r53-ip-updater
   User=your_username
   
   [Install]
   WantedBy=multi-user.target
   ```

2. Create a timer file at `/etc/systemd/system/route53-updater.timer`:
   ```ini
   [Unit]
   Description=Run Route 53 updater every hour
   
   [Timer]
   OnBootSec=5min
   OnUnitActiveSec=1h
   
   [Install]
   WantedBy=timers.target
   ```

3. Enable and start the timer:
   ```bash
   sudo systemctl enable route53-updater.timer
   sudo systemctl start route53-updater.timer
   ```

## AWS IAM Permissions

To follow the principle of least privilege, create an IAM policy with only the necessary permissions for this script. Here's a minimal IAM policy with fine-grained access control:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID"
            ],
            "Condition": {
                "ForAllValues:StringEquals": {
                    "route53:ChangeResourceRecordSetsRecordTypes": ["A"],
                    "route53:ChangeResourceRecordSetsActions": ["UPSERT"]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "route53:GetHostedZone",
                "route53:ListResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID"
            ]
        }
    ]
}
```

Replace `YOUR_HOSTED_ZONE_ID` with your actual hosted zone ID. 

This policy implements the following restrictions:

1. **Limited Record Types**: Only allows changes to 'A' records (IPv4 address records)
2. **Limited Actions**: Only allows the 'UPSERT' action (create if doesn't exist, update if exists)
3. **Specific Hosted Zone**: Restricts access to only the specified hosted zone

For even more restrictive access, you can limit changes to specific domain names by adding the `route53:ChangeResourceRecordSetsNormalizedRecordNames` condition. For example, to only allow updates to 'home.example.com':

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID"
            ],
            "Condition": {
                "ForAllValues:StringEquals": {
                    "route53:ChangeResourceRecordSetsNormalizedRecordNames": ["home.example.com"],
                    "route53:ChangeResourceRecordSetsRecordTypes": ["A"],
                    "route53:ChangeResourceRecordSetsActions": ["UPSERT"]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "route53:GetHostedZone",
                "route53:ListResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID"
            ]
        }
    ]
}
```

### Setting Up the IAM User/Role

1. Create a new IAM policy:
   - Go to IAM in the AWS Console
   - Navigate to Policies > Create policy
   - Use the JSON editor and paste the policy above
   - Name it something like "Route53UpdaterPolicy"

2. Create a new IAM user or role:
   - For a user: Go to Users > Add user
   - For a role: Go to Roles > Create role
   - Attach the policy you created
   - If creating a user for programmatic access, save the access key and secret key

3. Configure AWS credentials on your server:
   ```bash
   aws configure --profile route53-updater
   ```
   Then use `--profile route53-updater` when running the script.

## License

See the [LICENSE](LICENSE) file for details.
