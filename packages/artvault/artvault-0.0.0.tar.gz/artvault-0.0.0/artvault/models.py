import json

class Commission:
    def __init__(self, client, description, status='pending'):
        self.client = client
        self.description = description
        self.status = status

    def update_status(self, new_status):
        self.status = new_status

    def get_details(self):
        return f"{self.description} - {self.status}"

    def to_dict(self):
        return {
            'type': 'commission',
            'client': self.client,
            'description': self.description,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['client'], data['description'], data['status'])

class DigitalCommission(Commission):
    def __init__(self, client, description, software, status='pending'):
        super().__init__(client, description, status)
        self.software = software

    def get_details(self):
        return f"Digital: {self.description} using {self.software} - {self.status}"

    def to_dict(self):
        d = super().to_dict()
        d['type'] = 'digital'
        d['software'] = self.software
        return d

    @classmethod
    def from_dict(cls, data):
        return cls(data['client'], data['description'], data['software'], data['status'])

class TraditionalCommission(Commission):
    def __init__(self, client, description, medium, status='pending'):
        super().__init__(client, description, status)
        self.medium = medium

    def get_details(self):
        return f"Traditional: {self.description} in {self.medium} - {self.status}"

    def to_dict(self):
        d = super().to_dict()
        d['type'] = 'traditional'
        d['medium'] = self.medium
        return d

    @classmethod
    def from_dict(cls, data):
        return cls(data['client'], data['description'], data['medium'], data['status'])