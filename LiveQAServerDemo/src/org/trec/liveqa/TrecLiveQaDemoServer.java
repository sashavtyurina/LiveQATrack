package org.trec.liveqa;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;
import java.util.logging.Logger;
import java.util.logging.Handler;
import java.util.logging.FileHandler;
import java.util.logging.Level;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import fi.iki.elonen.NanoHTTPD;

import java.net.InetSocketAddress;
import java.nio.channels.AsynchronousServerSocketChannel;
import java.nio.channels.AsynchronousSocketChannel;
import java.nio.channels.CompletionHandler;
import java.nio.ByteBuffer;
import java.net.InetSocketAddress;
import java.io.*;
import java.util.concurrent.TimeUnit;

import java.util.concurrent.Future;
import java.util.concurrent.TimeoutException;
import java.lang.InterruptedException;
import java.util.concurrent.ExecutionException;
import java.net.SocketAddress;

import java.util.Arrays;

import org.json.*;

/**
 * Copyright 2015 Yahoo Inc.<br>
 * Licensed under the terms of the MIT license. Please see LICENSE file at the root of this project for terms.
 * <p/>
 * Sample server-side application for 2015 TREC LiveQA challenge.<br>
 * Usage: TrecLiveQaDemoServer [port-id]<br>
 * Stops on any input.
 * 
 * @author yuvalp@yahoo-inc.com
 * 
 */

/*The server that is responsible for sending the incoming question to the Python client and receive the answer*/


public class TrecLiveQaDemoServer extends NanoHTTPD {

    public static final String LOG_FILENAME = "POSTED_QUESTIONS.txt";
    public static final String PARTICIPANT_ID = "uwaterlooclarke";
    
    public static final String QUESTION_ID_PARAMETER_NAME = "qid";
    public static final String QUESTION_TITLE_PARAMETER_NAME = "title";
    public static final String QUESTION_BODY_PARAMETER_NAME = "body";
    public static final String QUESTION_CATEGORY_PARAMETER_NAME = "category";

    public static final String ANSWER_ROOT_ELEMENT_NAME = "xml";
    public static final String ANSWER_BASE_ELEMENT_NAME = "answer";
    public static final String ANSWER_PARTICIPANT_ID_ATTRIBUTE_NAME = "pid";
    public static final String ANSWER_ANSWERED_YES_NO_ATTRIBUTE_NAME = "answered";
    public static final String ANSWER_REPORTED_TIME_MILLISECONDS_ATTRIBUTE_NAME = "time";
    public static final String ANSWER_WHY_NOT_ANSWERED_ELEMENT_NAME = "discard-reason";
    public static final String ANSWER_CONTENT_ELEMENT_NAME = "content";
    public static final String ANSWER_RESOURCES_ELEMENT_NAME = "resources";
    public static final String RESOURCES_LIST_SEPARATOR = ",";
    public static final String NO_ANSWER = "no answer";

    public static final String YES = "yes";
    public static final String NO = "no";

    public static final String EXCUSE = "I just couldn't cut it :(";

    public static final int DEFAULT_PORT = 11000;
    public static final Locale WORKING_LOCALE = Locale.US;
    public static final String WORKING_TIME_ZONE_ID = "UTC";
    public static final TimeZone WORKING_TIME_ZONE = TimeZone.getTimeZone(WORKING_TIME_ZONE_ID);
    public static final Charset WORKING_CHARSET = StandardCharsets.UTF_8;

    private static final Logger logger = Logger.getLogger(TrecLiveQaDemoServer.class.getName());

    // private ByteBuffer incomingAnswer; // i don't think it's used here. 
    private int bufferSize = 1024;

    //let's try and create a separate instance of the AnswerServer for every question. 
    // private AnswerServer myAnswerServer;

    //AnswersServer - connects to Python code on port 11001, sends it incoming questions and 
    // awaits for answers

    public TrecLiveQaDemoServer(String hostname, int port) {
        super(hostname, port);
        // setupAnswerServer();
    }

    public TrecLiveQaDemoServer(int port) {
        super(port);
        // setupAnswerServer();
    }

    public void setupAnswerServer()
    {
        System.out.println("Setting up answer server");
        // incomingAnswer = ByteBuffer.allocate(bufferSize);
        // myAnswerServer = new AnswerServer();
    }

    @Override
    public Response serve(IHTTPSession session) {
        // extract get time from system
        final long getTime = System.currentTimeMillis();
        // logger.info("Got request at " + getTime);
        System.out.println("Got request");

        // read question data
        Map<String, String> files = new HashMap<>();
        Method method = session.getMethod();
        System.out.println("***Session:***");
        System.out.println(session.toString());
        if (Method.POST.equals(method)) {
            try {
                session.parseBody(files);
            } catch (IOException ioe) {
                return new Response(Response.Status.INTERNAL_ERROR, MIME_PLAINTEXT,
                                "SERVER INTERNAL ERROR: IOException: " + ioe.getMessage());
            } catch (ResponseException re) {
                return new Response(re.getStatus(), MIME_PLAINTEXT, re.getMessage());
            }
        }

        Map<String, String> params = session.getParms();
        String qid = params.get(QUESTION_ID_PARAMETER_NAME);
        String title = params.get(QUESTION_TITLE_PARAMETER_NAME);
        String body = params.get(QUESTION_BODY_PARAMETER_NAME);
        String category = params.get(QUESTION_CATEGORY_PARAMETER_NAME);
        String receivedQuestion = String.format("\nQID: %s\nTITLE: %s\nBODY: %s\nCATEGORY: %s\n", qid, title, body, category);
        
        if (category != null) {
            logger.info(receivedQuestion);    
        }
        else {
            System.out.println("This time the category is null");
        }
    

        // "get answer"
// we need to return Response object here. I don't want to go into detail of AnswerAndResources at the moment. 
// Given a question string receivedQuestion, we will construct a String resp using methods of our class AnswerServer.

        AnswerAndResources answerAndResources = null;
        try {
            // this is where we return our answer
            answerAndResources = getAnswerAndResources(qid, title, body, category);
        } catch (Exception e) {
            logger.warning("Failed to retrieve answer and resources");
            e.printStackTrace();
            return null;
        }


        // heer we wrap our answer in an appropriate format
        // initialize response document

        DocumentBuilderFactory docFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder docBuilder;
        try {
            docBuilder = docFactory.newDocumentBuilder();
        } catch (ParserConfigurationException e) {
            logger.warning("Could not build XML document");
            e.printStackTrace();
            return null;
        }

        Document doc = docBuilder.newDocument();
        Element rootElement = doc.createElement(ANSWER_ROOT_ELEMENT_NAME);
        doc.appendChild(rootElement);
        Element answerElement = doc.createElement(ANSWER_BASE_ELEMENT_NAME);
        rootElement.appendChild(answerElement);

        // populate fields
        if (answerAndResources != null) {
            answerElement.setAttribute(ANSWER_ANSWERED_YES_NO_ATTRIBUTE_NAME, YES);
            XmlUtils.addElementWithText(doc, answerElement, ANSWER_CONTENT_ELEMENT_NAME, answerAndResources.answer());
            XmlUtils.addElementWithText(doc, answerElement, ANSWER_RESOURCES_ELEMENT_NAME,
                            answerAndResources.resources());
            logger.info("Response: " + answerAndResources.answer() + "; Resources: " + answerAndResources.resources());
            // System.out.println("Response: " + answerAndResources.answer() + "; Resources: " + answerAndResources.resources());
        } else {
            answerElement.setAttribute(ANSWER_ANSWERED_YES_NO_ATTRIBUTE_NAME, NO);
            XmlUtils.addElementWithText(doc, answerElement, ANSWER_WHY_NOT_ANSWERED_ELEMENT_NAME, EXCUSE);
            logger.info("No answer given: " + EXCUSE);
            // System.out.println("No answer given: " + EXCUSE);
        }

        final long timeElapsed = System.currentTimeMillis() - getTime;
        answerElement.setAttribute(ANSWER_PARTICIPANT_ID_ATTRIBUTE_NAME, participantId());
        answerElement.setAttribute(ANSWER_REPORTED_TIME_MILLISECONDS_ATTRIBUTE_NAME, Long.toString(timeElapsed));
        answerElement.setAttribute(QUESTION_ID_PARAMETER_NAME, qid);
        logger.info("Internal time logged: " + timeElapsed);
        // System.out.println("Internal time logged: " + timeElapsed);

        String resp = XmlUtils.writeDocumentToString(doc);
/*End of process AnswerAndResources*/
        
    
        // we're creating a new instance of AnswerServer for every incoming question. 
        // when we're creating a new server we need to connect it to the Python server and that's it. 
        // also make sure that the Python server is able to accept multiple connections at a time. it should be i think.
        // move this part to getAnswersAndResources

        // AnswerServer myInstanceAnswerServer = new AnswerServer();
        // String resp = myInstanceAnswerServer.AskQuestion(receivedQuestion);

        // 
        // String resp = "our response";
        System.out.println("Got back to serve(). Response is ");
        // System.out.println(resp);

        return new Response(resp);
    }

    protected String participantId() {
        return PARTICIPANT_ID;
    }

    /**
     * Server's algorithmic payload.
     * 
     * @param qid unique question id
     * @param title question title (roughly 10 words)
     * @param body question body (could be empty, could be lengthy)
     * @param category (verbal description)
     * @return server's answer and a list of resources
     * @throws InterruptedException
     */
    protected AnswerAndResources getAnswerAndResources(String qid, String title, String body, String category)
                    throws InterruptedException {


        // String receivedQuestion = title + " " + body;

        AnswerServer myInstanceAnswerServer = new AnswerServer();
        // String resp = myInstanceAnswerServer.AskQuestion(receivedQuestion);
        String resp = myInstanceAnswerServer.AskQuestion(qid, title, body, category);

        String answer = "";
        String resources = "";
        try
        {
            JSONObject jresp = new JSONObject(resp);

            answer = jresp.getString("answer");
            resources = jresp.getString("source");
        }
        catch (JSONException e)
        {
            System.out.println(e);
            resp = NO_ANSWER; 
            return null;  
        }

        if (resp.equals(NO_ANSWER))
        {
            return null;
        }

        // TODO: split resp into answer and resources

        // String answer = resp;
        // String resources = "Resource1; Resourcse2"; 
        return new AnswerAndResources(answer, resources);
    }

    protected static class AnswerAndResources {

        private String answer;
        private String resources;

        public AnswerAndResources(String iAnswer, String iResources) {
            answer = iAnswer;
            resources = iResources;
        }

        public String answer() {
            return answer;
        }

        public String resources() {
            return resources;
        }

    }

    class AnswerServer {
        public static final int PORT_NUMBER = 11001;
        // public AsynchronousServerSocketChannel channel;
        public AsynchronousSocketChannel asyncSocketChannel;
        public ByteBuffer incomingAnswer;
        public Future <Integer> future_read;
        public String response = "default response";



        public AnswerServer(){
            try
            {
                // TODO: process exception here. If Python server is not running at the moment. ConnectionRefused occurs. 
                this.incomingAnswer = ByteBuffer.allocate(2024);
                this.asyncSocketChannel = AsynchronousSocketChannel.open();
                SocketAddress serverAddr = new InetSocketAddress("localhost", this.PORT_NUMBER);
                Future<Void> result = asyncSocketChannel.connect(serverAddr);
                result.get();
                System.out.println("Answer Server connected to Python Server.");
            }
            catch (Exception e)
            {
                System.out.println(e);
            }


            // try {
            //     this.incomingAnswer = ByteBuffer.allocate(2024);
            //     this.channel = AsynchronousServerSocketChannel.open().bind(new InetSocketAddress(this.PORT_NUMBER));
            //     this.channel.accept(null, new CompletionHandler<AsynchronousSocketChannel,Void>() {
            //     @Override
            //         public void completed(AsynchronousSocketChannel ch, Void att) {
            //             System.out.println("Yay! Established connection successfully.");
            //             asyncSocketChannel = ch;
            //             // HandleUserInput(ch);
            //             }
            //     @Override
            //         public void failed(Throwable exc, Void att) {
            //             System.out.println("failed to connect");
            //         }
            //     });
            // }
            // catch (IOException e ){
            //     System.out.println("exc in establishing a connection");
            // }
        }

        public String readMessage()
        {
            try
            {

                long timeout = 60;
                Integer future_read_code = future_read.get(timeout, TimeUnit.SECONDS);
                if (future_read.isDone())
                {

                    //only copying the bytes that have just arrived. Offset = 0, length = buffer.position.
                    //creating a new buffer to only contain the newly arrived information. 

                    //java's garbage collector will take care of the memory after we leave this function. 
                    //So there shouln't be any memory leaks. 
                    
                    System.out.println("Incoming Answer position is " + incomingAnswer.position());

                    //returns empty
                    // byte[] recent_response = new byte[incomingAnswer.position()];
                    // incomingAnswer.get(recent_response);

                    // returns empty 
                    // incomingAnswer.get(recent_response, 0, incomingAnswer.position()); 

                    byte[] full_buffer = incomingAnswer.array();
                    response = new String(Arrays.copyOfRange(full_buffer, 0, incomingAnswer.position()));
                    //works fine, but returns the entire contents of the buffer, which sometimes contains previous data
                    // response = new String(incomingAnswer.array());
                    // response = new String(recent_response);

                    // System.out.println("Reponse from Python server has come and it is: ");
                    // System.out.println(response);
                    this.asyncSocketChannel = this.asyncSocketChannel.shutdownInput();
                }
                else
                {
                    System.out.println("Future is not done.");
                }
            }
            catch ( TimeoutException e) 
            {
                System.out.println("Timeout exception ");
                response = NO_ANSWER;
            }
            catch (Exception e)
            {
                System.out.println("An exception in asking question occured!!!");
                System.out.println("If connection was reset by peer, then we must have run out of time");
                e.printStackTrace(System.out);
                response = NO_ANSWER;
                // System.out.println("exc in getting an answer");
            }

            return response; 
        }


        public String AskQuestion(String qid, String title, String body, String category)
        {
            // ByteBuffer message = ByteBuffer.wrap(question.getBytes());
            JSONObject jobj = new JSONObject();
            jobj.put("qid", qid);
            jobj.put("title", title);
            jobj.put("body", body);
            jobj.put("category", category);

            String question = jobj.toString();

            System.out.println("Asking a question");
            ByteBuffer message = ByteBuffer.wrap(question.getBytes());
            // System.out.println("Yahho is asking: " + question);

            //set response to an empty answer in case we don't have enough time to find an actual response. 
            response = "We didn't have enough time to come up with an aswer.";

            //sending message
            SentQuestionCompletionHandler handler = new SentQuestionCompletionHandler(this.asyncSocketChannel);
            this.asyncSocketChannel.write(message, null, handler);

            //waiting for a response to come in
            System.out.println("Waiting for respone to come in");
            while (! handler.gotResponse){
                // boolean voidFiller = handler.gotResponse;
                // System.out.println("Handler.got response is " + handler.gotResponse);
                // System.out.println("Some stuuuuff");

                //if the loop has println in it, everything works fine. Anything else instead of println gets stuck 
                // at this point. 
                //maybe if I try to put an operation that takes a long time it would help somehow. 
                //Will try sleep for 1 sec
                // Sleep operation seemed to help. No idea why though. 
                // 1 second maybe too long. I'll try to turn it down bit by bit and see what happens. 
                // down to 500 ms sleep - works fine. 
                // down to 250 ms sleep - also good. 
                // down to 100 ms sleep - ok. Leave it here. 

                try {
                    Thread.sleep(100); 
                } catch (InterruptedException ie) {
                    System.out.println("Exception in while the thread is sleeping. Deal with it later.");
                }
            }

            //now the response variable has a valid value in it 
            System.out.println("Returning response from Ask Question");

            try
            {
                System.out.println("Closing asyncSocketChannel");
                // safeclose here?
                this.asyncSocketChannel.close();
            }
            catch (IOException e )
            {
                System.out.println("Could not close the channel.");
                System.out.println(e);
            }
            return response;
        }

        class SentQuestionCompletionHandler implements CompletionHandler<Integer, ByteBuffer> 
        {

            AsynchronousSocketChannel channel;
            boolean gotResponse = false;

        public SentQuestionCompletionHandler(AsynchronousSocketChannel ch)
        {

            this.channel = ch;
        }

        @Override
        public void completed(Integer result, ByteBuffer message)
        {
            System.out.println("Successfully sent message. Awaiting for response.");

            // this resets the position, but all the old data is still in the buffer. 
            // solution1: clear all the old data in it first
            // solution2: keep track of how long the response it and only use those bytes. Then the old data won't matter.
            // Going with solution2. It is done in readMessage()

            incomingAnswer.clear();
            // future_read = null;

            future_read = this.channel.read(incomingAnswer);
            readMessage();
            
            this.gotResponse = true;
            System.out.println("gotResponse is true");
                // this.channel.read(incomingAnswer, 10, TimeUnit.SECONDS, null, new IncomingAnswerCompletionHandler(this.channel, incomingAnswer));
            // }
            // catch (InterruptedByTimeoutException e)
            // {
            //     System.out.println("Timeout.");
            // }
        }

        @Override
        public void failed(Throwable exc, ByteBuffer message)
        {
            System.out.println("Failed to send message");
            System.out.println(message);
        }
    }
}

    // ---------------------------------------------

    public static void main(String[] args) throws IOException {
        TrecLiveQaDemoServer server =
                        new TrecLiveQaDemoServer(args.length == 0 ? DEFAULT_PORT : Integer.parseInt(args[0]));

        Handler fh = new FileHandler(LOG_FILENAME);
        logger.addHandler(fh);
        logger.finest("Test message");

        server.start();
        System.in.read();
        server.stop();
    }

}
