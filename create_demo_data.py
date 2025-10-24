#!/usr/bin/env python3

"""
Create sample data for testing the subtask assignment functionality in the frontend.
This will create a realistic scenario with teams, tasks, and show how subtasks can be assigned.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, TeamMembership, Task, Subtask
from django.contrib.auth import get_user_model
from datetime import date, datetime
import uuid

def create_demo_data():
    """Create realistic demo data for testing subtask functionality"""
    print("Creating demo data for subtask testing...")
    
    # Create admin user if doesn't exist
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@company.com',
            'role': 'admin',
            'name': 'Ahmed Al-Mansouri',
            'first_name': 'Ahmed',
            'last_name': 'Al-Mansouri'
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✓ Created admin user: {admin_user.username}")
    
    # Create admin employee record
    admin_employee, created = Employee.objects.get_or_create(
        user=admin_user,
        defaults={
            'name': 'Ahmed Al-Mansouri',
            'position': 'System Administrator',
            'department': 'IT',
            'hire_date': date.today(),
            'salary': 10000.00,
            'phone': '+971501234567',
            'email': 'admin@company.com',
            'address': 'Dubai, UAE'
        }
    )
    
    # Create team manager
    manager_user, created = User.objects.get_or_create(
        username='team_manager',
        defaults={
            'email': 'manager@company.com',
            'role': 'manager',
            'name': 'Sara Al-Zahra',
            'first_name': 'Sara',
            'last_name': 'Al-Zahra'
        }
    )
    if created:
        manager_user.set_password('manager123')
        manager_user.save()
        print(f"✓ Created manager user: {manager_user.username}")
    
    manager_employee, created = Employee.objects.get_or_create(
        user=manager_user,
        defaults={
            'name': 'Sara Al-Zahra',
            'position': 'Development Team Lead',
            'department': 'Engineering',
            'hire_date': date.today(),
            'salary': 8500.00,
            'phone': '+971507654321',
            'email': 'manager@company.com',
            'address': 'Abu Dhabi, UAE'
        }
    )
    
    # Create team members
    developers = [
        {'username': 'dev1', 'name': 'Mohammed Hassan', 'position': 'Senior Frontend Developer'},
        {'username': 'dev2', 'name': 'Fatima Al-Rashid', 'position': 'Backend Developer'},
        {'username': 'dev3', 'name': 'Omar Al-Mahmoud', 'position': 'Full Stack Developer'},
        {'username': 'dev4', 'name': 'Aisha Al-Khalil', 'position': 'UI/UX Designer'}
    ]
    
    employees = []
    for i, dev in enumerate(developers):
        user, created = User.objects.get_or_create(
            username=dev['username'],
            defaults={
                'email': f"{dev['username']}@company.com",
                'role': 'employee',
                'name': dev['name'],
                'first_name': dev['name'].split()[0],
                'last_name': dev['name'].split()[1]
            }
        )
        if created:
            user.set_password('dev123')
            user.save()
            print(f"✓ Created developer user: {user.username}")
        
        employee, created = Employee.objects.get_or_create(
            user=user,
            defaults={
                'name': dev['name'],
                'position': dev['position'],
                'department': 'Engineering',
                'hire_date': date.today(),
                'salary': 6000.00 + (i * 500),  # Varying salaries
                'phone': f'+97150123456{i}',
                'email': f"{dev['username']}@company.com",
                'address': f'UAE Address {i+1}'
            }
        )
        employees.append(employee)
    
    # Create development team
    team, created = Team.objects.get_or_create(
        name='Web Development Team',
        defaults={
            'description': 'Responsible for web application development and maintenance',
            'team_leader': manager_employee,
            'created_by': admin_user,
            'is_active': True
        }
    )
    print(f"✓ Created team: {team.name}")
    
    # Add employees to team
    for i, employee in enumerate(employees):
        membership, created = TeamMembership.objects.get_or_create(
            team=team,
            employee=employee,
            defaults={
                'role': 'senior_member' if i == 0 else 'member',
                'is_active': True
            }
        )
    
    # Create a major project task
    main_task, created = Task.objects.get_or_create(
        title='E-Commerce Platform Redesign',
        defaults={
            'employee': employees[0],  # Assign to senior developer
            'description': '''Complete redesign and development of the company e-commerce platform.
            
This project involves:
- New modern UI/UX design
- Backend API improvements  
- Frontend React implementation
- Mobile responsiveness
- Performance optimization
- Security enhancements''',
            'status': 'doing',
            'priority': 'high',
            'date': date.today(),
            'created_by': manager_user,
            'assigned_by_manager': True,
            'team': team,
            'estimated_minutes': 2400  # 40 hours
        }
    )
    print(f"✓ Created main task: {main_task.title}")
    
    # Create subtasks with assignments
    subtasks_data = [
        {
            'title': 'UI/UX Design & Mockups',
            'description': 'Create comprehensive UI/UX designs and interactive mockups for all platform pages',
            'assigned_employee': employees[3],  # UI/UX Designer
            'priority': 'high',
            'estimated_minutes': 480,  # 8 hours
            'order': 1
        },
        {
            'title': 'Database Schema Design',
            'description': 'Design and implement new database schema with improved relationships and indexing',
            'assigned_employee': employees[1],  # Backend Developer
            'priority': 'high',
            'estimated_minutes': 360,  # 6 hours
            'order': 2
        },
        {
            'title': 'Backend API Development',
            'description': 'Develop RESTful API endpoints for products, orders, users, and payment processing',
            'assigned_employee': employees[1],  # Backend Developer
            'priority': 'high',
            'estimated_minutes': 720,  # 12 hours
            'order': 3
        },
        {
            'title': 'Frontend Components Development',
            'description': 'Build reusable React components for product listings, shopping cart, and checkout',
            'assigned_employee': employees[0],  # Senior Frontend Developer
            'priority': 'medium',
            'estimated_minutes': 600,  # 10 hours
            'order': 4
        },
        {
            'title': 'Payment Gateway Integration',
            'description': 'Integrate multiple payment gateways (Stripe, PayPal) with proper error handling',
            'assigned_employee': employees[2],  # Full Stack Developer
            'priority': 'high',
            'estimated_minutes': 360,  # 6 hours
            'order': 5
        },
        {
            'title': 'Mobile Responsive Implementation',
            'description': 'Ensure all components work perfectly on mobile devices and tablets',
            'assigned_employee': employees[0],  # Senior Frontend Developer
            'priority': 'medium',
            'estimated_minutes': 240,  # 4 hours
            'order': 6
        },
        {
            'title': 'Performance Optimization',
            'description': 'Optimize loading times, implement caching, and improve SEO',
            'assigned_employee': employees[2],  # Full Stack Developer
            'priority': 'medium',
            'estimated_minutes': 300,  # 5 hours
            'order': 7
        },
        {
            'title': 'Security Testing & Implementation',
            'description': 'Implement security best practices, OWASP guidelines, and conduct penetration testing',
            'assigned_employee': employees[1],  # Backend Developer
            'priority': 'urgent',
            'estimated_minutes': 360,  # 6 hours
            'order': 8
        },
        {
            'title': 'User Testing & Bug Fixes',
            'description': 'Coordinate user testing sessions and implement fixes based on feedback',
            'assigned_employee': employees[3],  # UI/UX Designer
            'priority': 'medium',
            'estimated_minutes': 240,  # 4 hours
            'order': 9
        },
        {
            'title': 'Documentation & Deployment',
            'description': 'Create technical documentation and handle production deployment',
            'assigned_employee': employees[2],  # Full Stack Developer
            'priority': 'low',
            'estimated_minutes': 180,  # 3 hours
            'order': 10
        }
    ]
    
    created_subtasks = []
    for subtask_data in subtasks_data:
        subtask, created = Subtask.objects.get_or_create(
            parent_task=main_task,
            title=subtask_data['title'],
            defaults=subtask_data
        )
        created_subtasks.append(subtask)
        if created:
            print(f"  ✓ Created subtask: {subtask.title} → {subtask.assigned_employee.name}")
    
    # Create another smaller task example
    smaller_task, created = Task.objects.get_or_create(
        title='Website Bug Fixes',
        defaults={
            'employee': employees[2],
            'description': 'Fix various bugs reported by users on the current website',
            'status': 'to_do',
            'priority': 'medium',
            'date': date.today(),
            'created_by': manager_user,
            'assigned_by_manager': True,
            'team': team,
            'estimated_minutes': 480  # 8 hours
        }
    )
    
    # Add some subtasks to the smaller task
    if created:
        print(f"✓ Created smaller task: {smaller_task.title}")
        
        small_subtasks = [
            {
                'title': 'Fix Login Form Validation',
                'description': 'Resolve validation issues with the login form',
                'assigned_employee': employees[0],
                'priority': 'high',
                'estimated_minutes': 90,
                'order': 1
            },
            {
                'title': 'Update Payment Form Styling',
                'description': 'Fix CSS issues with payment form on mobile devices',
                'assigned_employee': employees[3],
                'priority': 'medium',
                'estimated_minutes': 60,
                'order': 2
            }
        ]
        
        for subtask_data in small_subtasks:
            subtask, created = Subtask.objects.get_or_create(
                parent_task=smaller_task,
                title=subtask_data['title'],
                defaults=subtask_data
            )
            if created:
                print(f"  ✓ Created small subtask: {subtask.title} → {subtask.assigned_employee.name}")
    
    print(f"\n🎉 Demo data created successfully!")
    print(f"📊 Summary:")
    print(f"   - Teams: {Team.objects.count()}")
    print(f"   - Employees: {Employee.objects.count()}")
    print(f"   - Tasks: {Task.objects.count()}")
    print(f"   - Subtasks: {Subtask.objects.count()}")
    print(f"\n🔗 You can now test the subtask assignment functionality!")
    print(f"   - Login as admin (username: admin, password: admin123)")
    print(f"   - Login as manager (username: team_manager, password: manager123)")
    print(f"   - Login as developer (username: dev1, password: dev123)")
    print(f"   - Navigate to Tasks and click on the 'E-Commerce Platform Redesign' task")
    print(f"   - Click on 'Manage Subtasks' to see the assignment functionality in action")

if __name__ == '__main__':
    create_demo_data()