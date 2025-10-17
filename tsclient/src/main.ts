import net,{Socket } from "node:net";
import { Game} from "./game.js";
import { GameStatus } from "./enums/GameStatus.js";
import { json } from "node:stream/consumers";


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
			if (await Game.instance.start(PORT,HOST, client) == GameStatus.EXIT){
				//client.end()
			}
		}
	);
	
	client.on("data", async (data)=>{

		let response= JSON.parse(data.toString("utf-8").replace(/\n/g, ""));	
		

		//probably its better a switch sentence, a repository pattern is to much
		if (response.action == "login_ok"){
			
			Game.instance.setSessionToken(response.session_token, PORT, HOST)
			await Game.instance.start(PORT,HOST,client)	
		}
		
		 
		

	})
	

}catch(err){
	
	console.error("Unhandled error:", err);

}
