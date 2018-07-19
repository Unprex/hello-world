#open "graphics";;
#open "sys";;

let W_W, W_H, W_X, W_Y = 600, 400, 100, 50;;
open_graph ((string_of_int W_W) ^ "x" ^ (string_of_int W_H) ^ "+"
				^ (string_of_int W_X) ^ "+" ^ (string_of_int W_Y));;

(** INITIALISATIONS **)

let last_time = ref 0.;;
let rec mainloop () =
	let buffer = make_matrix W_H W_W (rgb 0 0 0) in

	(** MAIN LOOP **)

	(* Buffer display *)
	let buffer_img = make_image buffer in
	draw_image buffer_img 0 0;
	(* FPS display *)
	moveto 10 (W_H-22);
	let test_c = buffer.(16).(16) in
	set_color (test_c lxor 16777215);
	let cur_time = time () in
	draw_string (string_of_float (1. /. (cur_time -. !last_time)) ^ " FPS");
	last_time := cur_time;
	(* Keyboard inputs *)
	while key_pressed () do
		match read_key () with
		| s when s = char_of_int 27 -> raise Exit
		| s -> ()
	done;
	mainloop ();;

try mainloop () with
	| Exit -> ()
	| Graphic_failure _ -> ();;

close_graph ();;
