/** Parse SSE over arbitrary byte boundaries, including CRLF and multiline data. */
export async function consumeChatSse(reader, onEvent) {
 const decoder=new TextDecoder()
 let buffer=''
 function emit(block) {
  const data=block.split(/\r?\n/).filter(line=>line.startsWith('data:')).map(line=>line.slice(5).replace(/^ /,'')).join('\n')
  if(data && data!=='[DONE]')onEvent(JSON.parse(data))
 }
 try {
  while(true){
   const {done,value}=await reader.read()
   buffer += done ? decoder.decode() : decoder.decode(value,{stream:true})
   let match
   while((match=/\r?\n\r?\n/.exec(buffer))){emit(buffer.slice(0,match.index));buffer=buffer.slice(match.index+match[0].length)}
   if(done){if(buffer.trim())emit(buffer);break}
  }
 } finally { await reader.cancel().catch(()=>{});reader.releaseLock() }
}
