import net,{Socket } from "node:net";
import { Game} from "./game.js";
import { GameStatus } from "./enums/GameStatus.js";
import { json } from "node:stream/consumers";
import { getRandomValues } from "node:crypto";


const PORT: number = 5000;
const HOST: string ="127.0.0.1" ; 
try{
	const client:Socket = net.createConnection({ port: PORT, host: HOST });

	client.on("error", 
		
		(err: NodeJS.ErrnoException)=>{
			
			if (err.errno == -4078){
			
				console.error("Connection refused")
				
				return
			}
			
			console.error(err.code)
		}
	
	);
	
	
	client.on("connect", 
		
		async ()=>
		{
			
			let game : GameStatus = await Game.instance.runClient(PORT,HOST, client)
			
			console.debug(`connect -> status${game}`)

			if ( game == GameStatus.EXIT){
				
				client.end()
			
			}

			if(game == GameStatus.NOTHING){
			
			}
		}
	);
	
	client.on("data", async (data)=>{

		let response= JSON.parse(data.toString("utf-8").replace(/\n/g, ""));	
		
		let game : GameStatus = await Game.instance.runClient(PORT,HOST,client,response)
		
		console.debug(`data -> status${game}`)
		
		if ( game == GameStatus.EXIT){

			console.error("sali")	
			
			client.end()
		}

		if(game == GameStatus.NOTHING){}

	})
	

}catch(err){
	
	console.error("Unhandled error:", err);

}
