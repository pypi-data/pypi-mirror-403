# OAuth

Types:

```python
from hammerhead.types import OAuthExchangeTokenResponse
```

Methods:

- <code title="get /oauth/authorize">client.oauth.<a href="./src/hammerhead/resources/oauth.py">authorize</a>(\*\*<a href="src/hammerhead/types/oauth_authorize_params.py">params</a>) -> None</code>
- <code title="post /oauth/deauthorize">client.oauth.<a href="./src/hammerhead/resources/oauth.py">deauthorize</a>(\*\*<a href="src/hammerhead/types/oauth_deauthorize_params.py">params</a>) -> None</code>
- <code title="post /oauth/token">client.oauth.<a href="./src/hammerhead/resources/oauth.py">exchange_token</a>(\*\*<a href="src/hammerhead/types/oauth_exchange_token_params.py">params</a>) -> <a href="./src/hammerhead/types/oauth_exchange_token_response.py">OAuthExchangeTokenResponse</a></code>

# Activities

Types:

```python
from hammerhead.types import (
    ActivitySummary,
    Pagination,
    ActivityRetrieveResponse,
    ActivityListResponse,
)
```

Methods:

- <code title="get /activities/{activityId}">client.activities.<a href="./src/hammerhead/resources/activities.py">retrieve</a>(activity_id) -> <a href="./src/hammerhead/types/activity_retrieve_response.py">ActivityRetrieveResponse</a></code>
- <code title="get /activities">client.activities.<a href="./src/hammerhead/resources/activities.py">list</a>(\*\*<a href="src/hammerhead/types/activity_list_params.py">params</a>) -> <a href="./src/hammerhead/types/activity_list_response.py">ActivityListResponse</a></code>
- <code title="get /activities/{activityId}/file">client.activities.<a href="./src/hammerhead/resources/activities.py">retrieve_file</a>(activity_id) -> BinaryAPIResponse</code>

# Routes

Types:

```python
from hammerhead.types import RouteSummary, RouteListResponse
```

Methods:

- <code title="get /routes">client.routes.<a href="./src/hammerhead/resources/routes/routes.py">list</a>(\*\*<a href="src/hammerhead/types/route_list_params.py">params</a>) -> <a href="./src/hammerhead/types/route_list_response.py">RouteListResponse</a></code>
- <code title="delete /routes/{routeId}">client.routes.<a href="./src/hammerhead/resources/routes/routes.py">delete</a>(route_id) -> None</code>

## File

Types:

```python
from hammerhead.types.routes import Route
```

Methods:

- <code title="post /routes/file">client.routes.file.<a href="./src/hammerhead/resources/routes/file.py">create</a>(\*\*<a href="src/hammerhead/types/routes/file_create_params.py">params</a>) -> <a href="./src/hammerhead/types/routes/route.py">Route</a></code>
- <code title="put /routes/{routeId}/file">client.routes.file.<a href="./src/hammerhead/resources/routes/file.py">update</a>(route_id, \*\*<a href="src/hammerhead/types/routes/file_update_params.py">params</a>) -> <a href="./src/hammerhead/types/routes/route.py">Route</a></code>

# Workouts

Methods:

- <code title="delete /workouts/{workoutId}">client.workouts.<a href="./src/hammerhead/resources/workouts/workouts.py">delete</a>(workout_id) -> None</code>

## File

Types:

```python
from hammerhead.types.workouts import Workout
```

Methods:

- <code title="post /workouts/file">client.workouts.file.<a href="./src/hammerhead/resources/workouts/file.py">create</a>(\*\*<a href="src/hammerhead/types/workouts/file_create_params.py">params</a>) -> <a href="./src/hammerhead/types/workouts/workout.py">Workout</a></code>
- <code title="put /workouts/{workoutId}/file">client.workouts.file.<a href="./src/hammerhead/resources/workouts/file.py">update</a>(workout_id, \*\*<a href="src/hammerhead/types/workouts/file_update_params.py">params</a>) -> <a href="./src/hammerhead/types/workouts/workout.py">Workout</a></code>
