# Feel about AI Power to build a project

### online-doc
- Build an simple online web document system. 
- The system allows user to create its own doc.
- The system also allows multiple users to edit the same document simultaneously


### Functional requirements
- As a user, I could create/delete the doc
- As a user A, I could add words into docA
- As a user B, I could add words into docA


### Tech Requirements
- use docker + docker-compose for local development

- Easy to deploy to k8s cluster

- Use Postgres DB for data consistency

- FrontEnd Side
  - Use React + next.js to implement UI part

- Backend Side
  - Use python as the programme language to handle the restful api calls
  - Use `uv` as python dependencies management tools
  - Use class pattern to write python code

- Database
  - Use Postgres DB for data consistency

- Deployment
  - Easy to deploy to k8s cluster

### non-functional requirements

- Business objective
  - 1m daily active users
  - 2m messages need to be handle daily
  - cross region requirements

- System objective
  - monitoring
  - logs
  - auto-scaling
  - latency
  - consistency
  - relibility
  - cost


/speckit.plan 
- use docker + docker-compose for local development
- Easy to be deployed to k8s cluster
- Use Postgres DB for data consistency (local use postgres docker)
- FrontEnd Side
  - Use React + next.js to implement UI logic
  - Use bootstrap as the UI framework
- Backend Side
  - Use python as the programme language to handle the restful api calls
  - Use `uv` as python dependencies management tools
  - Use class pattern to write python code
