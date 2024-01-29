POST 	/sessions				[]					- login
{
	"email": string,
	"password": string,
}
-> 200	["Authorization": string]		{}					- success
-> 400	[]					{}					- bad request
-> 401	[]					{}					- bad credentials
-> 500	[]					{"error": string}			- internal server error

DELETE 	/sessions				["Authorization": string]		- logout
-> 200	[]
-> 400	[]
-> 500	[]

POST	/users					["Authorization": string]		- register
{
	"email": string,
	"password": string,
	"firstname": string,
	"lastname": string,
	"gender": string,
	"city": string,
	"country": string,
}
-> 200	[]
-> 400	[]
-> 500	[]

GET	/users/<user-email>			["Authorization": string]		- get user data
-> 200	[]
{
	"email": string,
	"password": string,
	"firstname": string,
	"lastname": string,
	"gender": string,
	"city": string,
	"country": string,
}
-> 400	[]
-> 500	[]

GET	/users/<user-email>/posts		["Authorization": string]		- get user posts
-> 200	[]
-> 400	[]
-> 500	[]

POST	/users/<user-email>			["Authorization": string]		- change password
-> 200	[]
-> 400	[]
-> 500	[]

POST	/users/<user-email>/posts		["Authorization": string]		- create a new post on user wall
-> 200	[]
-> 400	[]
-> 500	[]

DELETE	/users/<user-email>/posts/<post-id>	["Authorization": string]		- delete existing post
-> 200	[]
-> 400	[]
-> 500	[]
