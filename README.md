# Pipeline Reporter


## Description

This is a repo to host, manage, and maintain a small project that automatically creates a readable report of given projects.

The purpose of which is to more effectively and more quickly find, diagnose, address, and manage overnight issues caught in scheduled nightly jobs in our pipelines 

**NOTE: This is currently tooled for GitLab CI, adding an issue to track to make agnostic of CI platform or at least allow for GitHub usage**
## Setup

Note that you will need to create a logs and reports blank directory on the project root in order for this work correctly

## Usage

1. Add the projects by CI_PROJECT_NAME format to the repos.txt file
2. Run using the API Url as the --url parameter
```
python reporter.py --url $CI_PROJECT_API_URL 
```
