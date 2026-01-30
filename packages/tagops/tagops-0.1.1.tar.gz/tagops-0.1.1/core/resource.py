class EC2Resource:
    def __init__(self, instance_id, name, state, region):
        self.instance_id = instance_id
        self.name = name
        self.state = state
        self.region = region

        # Existing associated resources
        self.eips = []
        self.security_groups = []
        self.keypair = None

        # Protection flags
        self.stop_protected = False
        self.terminate_protected = False

        # EBS
        self.volumes = []
        self.snapshots = []

        # 🔹 NEW: ENIs
        # [{id, status, primary}]
        self.enis = []

        # ASG membership
        self.asg_name = None


class ASGResource:
    def __init__(self, name, region, min_size, max_size, desired_capacity, original_min_size=None, original_max_size=None, original_desired_capacity=None):
        self.name = name
        self.region = region
        self.min_size = min_size
        self.max_size = max_size
        self.desired_capacity = desired_capacity
        self.tags = []
        self.launch_template_id = None
        
        # Store original values for restoration (from tags or current)
        self.original_min_size = original_min_size if original_min_size is not None else min_size
        self.original_max_size = original_max_size if original_max_size is not None else max_size
        self.original_desired_capacity = original_desired_capacity if original_desired_capacity is not None else desired_capacity
