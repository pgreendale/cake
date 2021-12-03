/*
	Passive 7-seg decoder with base switching (small logic footprint but much switching)
	
	12/2021, HTWK LABP, Vincent Weiß
	@param base 		basis of digits (8,10,16 actually)
	@param digits 		number of digits used (act upon select_o and data_i width
	@param freq_in		redefine clock frequency
	@param freq_disp	redefine display refresh rate
	
	@input clk_i 		clock input 
	@input data_i		data input, assumed 1 Nibble per digit, even if digit has domain< 4bit per digit 
	@output segment_o 7 segment display output, positive active, MSB-to-LSB: DP,g,f,e,d,c,b,a
	@output select_o  digit select lines, one-hot, positive active, width depends on digit 

	TODO: 
		input latching
*/

module decoder_7seg_b16(
	input [3:0] data_i,
	output reg [6:0] seg_o
);
	always@(data_i)begin
		case (data_i)
			'b0000		: seg_o =  'b0111111;	//"0"
			'b0001		: seg_o =  'b0000110;	//"1"
			'b0010		: seg_o =  'b1011011;	//"2"
			'b0011		: seg_o =  'b1001111;	//"3"
			'b0100		: seg_o =  'b1100110;	//"4"
			'b0101		: seg_o =  'b1101101;	//"5"
			'b0110		: seg_o =  'b1111101;	//"6"
			'b0111		: seg_o =  'b0000111;	//"7"
			'b1000		: seg_o =  'b1111111;	//"8"
			'b1001		: seg_o =  'b1101111;	//"9"
			'b1010		: seg_o =  'b1110111;	//"A"
			'b1011		: seg_o =  'b1111100;	//"b"
			'b1100		: seg_o =  'b0111001;	//"C"
			'b1101		: seg_o =  'b1011110;	//"d"
			'b1110 		: seg_o =  'b1111001;	//"E"
			'b1111		: seg_o =  'b1110001;	//"F"
		//default		: seg_0 =  0b0100000;	//unknown, display "-"
		endcase
	end
	initial
		$display("7 Seg decoder with basis 16 (hex) generated"); 
endmodule 
module decoder_7seg_b10(
	input [3:0] data_i,
	output reg [6:0] seg_o
);
	always@(data_i)begin
		case (data_i)
			'b0000		: seg_o =  'b0111111;	//"0"
			'b0001		: seg_o =  'b0000110;	//"1"
			'b0010		: seg_o =  'b1011011;	//"2"
			'b0011		: seg_o =  'b1001111;	//"3"
			'b0100		: seg_o =  'b1100110;	//"4"
			'b0101		: seg_o =  'b1101101;	//"5"
			'b0110		: seg_o =  'b1111101;	//"6"
			'b0111		: seg_o =  'b0000111;	//"7"
			'b1000		: seg_o =  'b1111111;	//"8"
			'b1001		: seg_o =  'b1101111;	//"9"
			default		: seg_o =  'b1000000;	//unknown, display "-"
		endcase
	end
	initial
		$display("7 Seg decoder with basis 10 (dec) generated");
endmodule 

module decoder_7seg_b8(
	input [2:0] data_i,
	output reg [6:0] seg_o
);
	always@(data_i)begin
		case (data_i)
			'b0000		: seg_o =  'b0111111;	//"0"
			'b0001		: seg_o =  'b0000110;	//"1"
			'b0010		: seg_o =  'b1011011;	//"2"
			'b0011		: seg_o =  'b1001111;	//"3"
			'b0100		: seg_o =  'b1100110;	//"4"
			'b0101		: seg_o =  'b1101101;	//"5"
			'b0110		: seg_o =  'b1111101;	//"6"
			'b0111		: seg_o =  'b0000111;	//"7"
			//default		: seg_o =  0b0100000;	//unknown, display "-"
		endcase
	end
	initial
		$display("7 Seg decoder with basis 8 (octal) generated"); 
endmodule
module decoder#(
	parameter base = 16
	)(
	input clk,
	input [3:0] data_i,
	output[6:0] seg_o
);
	generate
		case(base)
			 8			: decoder_7seg_b8  dec_7Seg_b8  (.data_i(data_i),.seg_o(seg_o));
			10			: decoder_7seg_b10 dec_7Seg_b10 (.data_i(data_i),.seg_o(seg_o));
			16			: decoder_7seg_b16 dec_7Seg_b16 (.data_i(data_i),.seg_o(seg_o));
			default	: assign seg_o = data_i ; //go straight through
		endcase 
	endgenerate 
endmodule

/*
Main Module
*/ 
module decoder_7seg#(
	parameter base     = 16,				//base to convert to
	parameter digits   = 4,					//number of digits 
	parameter freq_in  = 12*1000000, 	//input clock frequency 
	parameter freq_disp= 1000				//display frequency 
	)(
	input clk_i,
	input [digits*4-1:0] data_i,
	output[7:0] 			segment_o,
	output[digits-1:0]	select_o 
);
//instantiate decoder
decoder #(
	.base(base)
	)decoder(
	.data_i(digit_temp),
	.seg_o(decoder_out),
); 
/*
	*Display refresh clock generator (LEDs cant run with high clocks)
*/
reg clk_displ; 
reg [$clog2(digits*freq_in/freq_disp)-1:0] divcounter_displ; 
always@(posedge clk_i)begin 
	if (divcounter_displ < digits*freq_in/freq_disp)
		divcounter_displ <= divcounter_displ +1; 
	else begin 
		divcounter_displ <= 'd0;
		clk_displ <= ~clk_displ; 
	end 
end
initial begin 
	clk_displ 			<= 1'b0;  	
	divcounter_displ	<= 'd0;
	display_buf 		<= 'd0; 
	display_sel 		<= 'd0; 
end 

//digit mux
reg  [1:0] digit_select; 	//digit selector 
reg  [3:0] digit_temp;		//holding selected 
wire [6:0] decoder_out; 
reg  [7:0] display_buf; 
reg  [7:0] display_sel;
always@(posedge clk_displ) begin
		digit_select  <= digit_select + 1;
		display_sel	<= 1 << digit_select;
		display_buf <= decoder_out;
end 	
assign segment_o 	= display_buf;
assign select_o	= display_sel;

always@(*) begin 
		case(digit_select)
			'd0 : digit_temp = data_i % `DISPLAY_BASE;
			'd1 : digit_temp = (data_i / `DISPLAY_BASE ) % `DISPLAY_BASE;
			'd2 : digit_temp = ((data_i / `DISPLAY_BASE)/`DISPLAY_BASE)%`DISPLAY_BASE;
			'd3 : digit_temp = (((data_i / `DISPLAY_BASE)/`DISPLAY_BASE)/`DISPLAY_BASE)%`DISPLAY_BASE;
		endcase
end
endmodule 

