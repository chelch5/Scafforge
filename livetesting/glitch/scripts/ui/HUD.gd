extends CanvasLayer

# HUD.gd - Handles glitch telegraph warnings and UI display
# Connected to GlitchState.glitch_warning signal

const TELEGRAPH_SCENE = preload("res://scenes/glitch/TelegraphEffect.tscn")
const TELEGRAPH_DURATION_SEC = 2.0

func _ready() -> void:
	print("[HUD] Connecting to GlitchState.glitch_warning")
	var connect_result = GlitchState.connect("glitch_warning", Callable(self, "_on_glitch_warning"))
	if connect_result != OK:
		push_warning("[HUD] Failed to connect to glitch_warning signal: %d" % connect_result)
	else:
		print("[HUD] Successfully connected to glitch_warning signal")

func _on_glitch_warning(event_id: String) -> void:
	print("[HUD] Received glitch_warning for event: %s" % event_id)
	
	# Instance the telegraph effect
	var telegraph = TELEGRAPH_SCENE.instantiate()
	add_child(telegraph)
	
	# Update the label text with event context if it has a WarningLabel child
	var warning_label = telegraph.get_node_or_null("WarningLabel")
	if warning_label != null:
		warning_label.text = "GLITCH WARNING: %s" % event_id
	
	# Remove the telegraph after duration using a Timer
	var timer = Timer.new()
	timer.wait_time = TELEGRAPH_DURATION_SEC
	timer.one_shot = true
	telegraph.add_child(timer)
	timer.timeout.connect(_on_telegraph_timeout.bind(telegraph))
	timer.start()

func _on_telegraph_timeout(telegraph: Node) -> void:
	if is_instance_valid(telegraph):
		telegraph.queue_free()
