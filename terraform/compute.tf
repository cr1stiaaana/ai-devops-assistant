# terraform/ compute.tf




resource "aws_security_group" "ec2" {

    name = "${var.project_name}-sg"
    description = "Security group for EC2 instance"
    vpc_id = aws_vpc.main.id


    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]

    }

    tags = {
        Name = "${var.project_name}-sg"
        Project = var.project_name
    }
}


resource "aws_instance" "main" {
    ami = "ami-0720a3ca2735bf2fa"
    instance_type = "t2.micro"
    subnet_id = aws_subnet.public.id
    vpc_security_group_ids = [aws_security_group.ec2.id]

    tags = {
        Name = "${var.project_name}-ec2"
        Project = var.project_name
    }
}