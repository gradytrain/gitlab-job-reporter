{% for report in reports %}
## Project Name: {{ report.proj_name }} <br>
Project ID: {{ report.proj_id }} 
Pipeline ID: {{ report.id }} 
Created At: {{ report.created_at }} 

{% if report.status == "failed" %}
#### Pipeline Status: <span style="color:red;font-size: 200%"> {{ report.status }} </span><br> 
{% else %}
#### Pipeline Status: <span style="color:green"> {{ report.status }} </span><br> 
{% endif %}
#### URL: {{ report.url }} <br>
<br>

{% endfor %}