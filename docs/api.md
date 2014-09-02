# Centinel server spec

* version: 0.0.1
* author: gsathya

## Version
### `GET /version`

* Get the latest recommended version of Centinel

```
➜  ~  curl -i http://127.0.0.1:5000/version

HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 20
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:00:42 GMT

{
  "version": 1.1
}
```

## Register
### `POST /register`

* Create a new user
* Ex - `username: foo` and `password: bar`

```
➜  ~  curl -i -H "Content-Type: application/json" -X POST -d '{"username":"foo", "password":"bar"}' http://127.0.0.1:5000/register

HTTP/1.0 201 CREATED
Content-Type: application/json
Content-Length: 25
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:01:59 GMT

{
  "status": "success"
}
```

* Creating the same user again

```
➜  ~  curl -i -H "Content-Type: application/json" -X POST -d '{"username":"foo", "password":"bar"}' http://127.0.0.1:5000/register

HTTP/1.0 400 BAD REQUEST
Content-Type: application/json
Content-Length: 28
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:02:25 GMT

{
  "error": "Bad request"
}
```

## Results
### `GET /results`

* Download all the result files.
* Requires authentication

```
➜  ~  curl -u foo:bar -i -H "Content-Type: application/json"  http://127.0.0.1:5000/results

Content-Type: application/json
Content-Length: 1136659
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:05:53 GMT

{
  "results": {
    "result-2014-09-01T22:21:14.306037": {
      "http_request": [
        {...}
      ]
  }
}
        
```

### `POST /results`

* Upload a result file
* Requires authentication

```
➜  ~  curl -i -u foo:bar -0 -X POST -F files='{"result": {"status": "success"}}' http://127.0.0.1:5000/results

HTTP/1.0 201 CREATED
Content-Type: application/json
Content-Length: 28
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:40:52 GMT

{
  "status": "success"
}
        
```

## Experiments
### `GET /experiments`

* Get names of experiment files in the server
* Requires authentication

```
➜  ~  curl -u foo:bar -i -H "Content-Type: application/json"  http://127.0.0.1:5000/experiments

HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 65
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:15:12 GMT

{
  "experiments": [
    "tcp_connect",
    "http_request"
  ]
}
```

### `GET /experiments/<experiment>`

* Download `<experiment>` file
* Requires authentication

```
➜  ~  curl -u foo:bar -i -H "Content-Type: application/json"  http://127.0.0.1:5000/experiments/http_request

HTTP/1.0 200 OK
Content-Length: 549
Content-Type: text/x-python; charset=utf-8
Last-Modified: Tue, 02 Sep 2014 03:14:54 GMT
Cache-Control: public, max-age=43200
Expires: Tue, 02 Sep 2014 15:16:50 GMT
ETag: "flask-1409627694.0-549-267654249"
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:16:50 GMT

import centinel.primitives.http as http

from centinel.experiment import Experiment

class HTTPRequestExperiment(Experiment):
    name = "http_request"

    def __init__(self, input_file):
        self.input_file  = input_file
        self.results = []
        self.host = None
        self.path = "/"

    def run(self):
        for line in self.input_file:
            self.host = line.strip()
            self.http_request()

    def http_request(self):
        result = http.get_request(self.host, self.path)
        self.results.append(result)
```        


## Clients
### `GET /clients`

* Download all client names
* Requires authentication
```
➜  ~  curl -u foo:bar -i http://127.0.0.1:5000/clients

HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 77
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 02 Sep 2014 03:44:24 GMT

{
  "clients": [
    "d65ab701-2bb3-440f-b12d-b80a508413c1",
    "foo"
  ]
}
```
