

SENSORS = ["temp", "hum", "water_level"]
CONTROLS = ["switch_01", "switch_02"]
ACTION_PREFIX = "action_"
READ_PREFIX = "read_"


def get_read_method_name(string):
    items = string.split("_")
    return f"read{''.join([item.capitalize() for item in items])}()"


def generate(sensors: list, controls: list, tft=False, ):
    fill_response_sensors = "\n".join([
        f"    response[\"{item}\"] = {get_read_method_name(item)};" for item in sensors
    ])
    fill_response_controls = "\n".join([
        f"    response[\"{item}\"] = readPin({item.upper()});" for item in controls
    ])

    read_methods = "\n\n".join([
        f"""float {get_read_method_name(item)} {{
    // TODO: implement
}}""" for item in sensors
    ])

    else_if_clauses_controls = "\n".join([
        f"""
    }} else if (request == action_prefix + \"{item}\") {{
        togglePin({item.upper()});
        response[\"{item}\"] = readPin({item.upper()});""" for item in controls
    ])

    else_if_clauses_sensors = "\n".join([
        f"""
    }} else if (request == read_prefix + \"{item}\") {{
        response[\"{item}\"] = {get_read_method_name(item)};""" for item in sensors
    ])

    pins_c = "\n".join([
        f"#define {item.upper()} <X> // TODO: set pin number" for item in controls
    ])

    setup_pins = "\n".join([
        f"    pinMode({item.upper()}, OUTPUT);" for item in controls
    ])

    template = f"""
#include <Arduino_JSON.h>


// Define pins
{pins_c}


int readPin(int PIN) {{
    return digitalRead(PIN);
}}

void togglePin(int PIN) {{
  if (readPin(PIN)) {{
    digitalWrite(PIN, LOW);
  }} else {{
    digitalWrite(PIN, HIGH);
  }}
}}

void handleStatus() {{
    JSONVar response;
    response["status"] = "ok";
{fill_response_sensors}
{fill_response_controls}
    sendResponse(JSON.stringify(response));
}}

void handleAction(String body) {{

    JSONVar myObject = JSON.parse(body);
    
    if (JSON.typeof(myObject) == "undefined") {{
        handleError("Parsing JSON failed.");
        return;
    }}
    if (!myObject.hasOwnProperty("request")) {{
        handleError("JSON needs to have exactly one keyword <request>");
        return;
    }}

    String read_prefix = "{READ_PREFIX}";
    String action_prefix = "{ACTION_PREFIX}";
    String request = (const char*) myObject["request"];
    if (request == "status") {{
       handleStatus();
       return;
    }}
    
    JSONVar response;
    if (request == "info") {{
        response["uuid"]= getUuid();
{else_if_clauses_controls}
{else_if_clauses_sensors}

    }} else {{
        handleError("UNKNOWN_CMD " + request);
        return;
    }}
    response["status"] = "ok";
    sendResponse(JSON.stringify(response));
}}

void handleError(String msg) {{
    JSONVar message;
    // TODO: implement custom error fields
    message["cause"] = msg;
    
    sendResponse(JSON.stringify(message));
}}

//=====================  sensors  =====================//

void sendResponse(String body) {{
    // TODO: implement
}}

String getUuid() {{
    // TODO: implement
}}

{read_methods}


//======================  setup  ======================//

void setup(void) {{
{setup_pins}

    // TODO: set-up sensor pins

    // TODO: setup communication
    // TODO: setup display
}}

//======================  loop  ======================//

void loop(void) {{
  // TODO: implement
}}
"""
    return template


if __name__ == "__main__":
    print(generate(SENSORS, CONTROLS))
