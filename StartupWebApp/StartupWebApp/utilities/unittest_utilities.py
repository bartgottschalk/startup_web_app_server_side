def validate_response_is_OK_and_JSON(context, response):
    # print("hi from validate_response_is_OK_and_JSON")
    context.assertEqual(response.status_code, 200)
    context.assertEqual(response['content-type'], 'application/json')
    return
