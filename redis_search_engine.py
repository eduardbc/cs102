import redis

def multi_lookup(index, query):
    #print index
    temp_list=[]
    out_list=[]
    dict={}
    for word in query:
       temp_list = temp_list + lookup(index,word)
       #print "----"
    #print temp_list
    #print "-----"
    for url in temp_list:
        #print "print word: " + str(url)
        if url[0] in dict:
            dict[url[0]].append(url[1])
        else:
            dict[url[0]]=[url[1]]
    #print "print dic"
    #print dict
    for url in dict:
       positions=dict[url]
       #print "positions: "+str(positions)

       query_len=len(query)
       #print "query_len: "+str(query_len)

       result_len=len(positions)
       #print "result_len: "+str(result_len)

       if result_len == query_len:
          positions_ordered=sorted(positions)
          #print "positions_ordered: "+str(positions_ordered)

          offset=0
          #print "range: " + str(range(4,5))
          word_positions=range(positions_ordered[0], positions_ordered[0]+query_len)
          #print "word_positions: " + str(word_positions)
          for i in range(0,query_len):
            if positions_ordered[offset] == word_positions[offset]:
              offset=offset+1
              #print "offset: " + str(offset)
              #print "query_len-1: " + str(query_len-1)
          if offset==query_len:
              out_list.append(url)
    #print "Llista final : " + str(out_list)  
    return out_list


def compute_ranks():
    graph={}
    graph_conn = redis.Redis(host="localhost", db=3)
    rank_conn = redis.Redis(host="localhost", db=4)
    d = 0.8 # damping factor
    numloops = 10
    #be need to get the graph to make the ranks
    #here we obtain all the key
    graph_keys=graph_conn.keys("*")
    #For each key we get the values
    for key in graph_keys:
        graph[key]=graph_conn.lrange(key,0,-1)
    for i in graph:
        print "Key: " + i
        print  "VALUES :             " + str(graph[i])
    print "------"
    print graph
    
    ranks = {}
    npages = len(graph)
    print "pages start-----"
    for page in graph:
        print page
        ranks[page] = 1.0 / npages
    print "pages end--------"
    
    for i in range(0, numloops):
        newranks = {}
        for page in graph:
            newrank = (1 - d) / npages
            for node in graph:
                if page in graph[node]:
                    newrank= newrank + d *  ranks[node] / len(graph[node])
                    
                        
            newranks[page] = newrank
            print page + "     " + str(newrank)
            rank_conn.set(page,newrank)
        ranks = newranks
    return ranks



cache = {
   'http://udacity.com/cs101x/urank/index.html': """<html>
<body>
<h1>Dave's Cooking Algorithms</h1>
<p>
Here are my favorite recipies:
<ul>
<li> <a href="http://udacity.com/cs101x/urank/hummus.html">Hummus Recipe</a>
<li> <a href="http://udacity.com/cs101x/urank/arsenic.html">World's Best Hummus</a>
<li> <a href="http://udacity.com/cs101x/urank/kathleen.html">Kathleen's Hummus Recipe</a>
</ul>

For more expert opinions, check out the 
<a href="http://udacity.com/cs101x/urank/nickel.html">Nickel Chef</a> 
and <a href="http://udacity.com/cs101x/urank/zinc.html">Zinc Chef</a>.
</body>
</html>






""", 
   'http://udacity.com/cs101x/urank/zinc.html': """<html>
<body>
<h1>The Zinc Chef</h1>
<p>
I learned everything I know from 
<a href="http://udacity.com/cs101x/urank/nickel.html">the Nickel Chef</a>.
</p>
<p>
For great hummus, try 
<a href="http://udacity.com/cs101x/urank/arsenic.html">this recipe</a>.

</body>
</html>






""", 
   'http://udacity.com/cs101x/urank/nickel.html': """<html>
<body>
<h1>The Nickel Chef</h1>
<p>
This is the
<a href="http://udacity.com/cs101x/urank/kathleen.html">
best Hummus recipe!
</a>

</body>
</html>






""", 
   'http://udacity.com/cs101x/urank/kathleen.html': """<html>
<body>
<h1>
Kathleen's Hummus Recipe
</h1>
<p>

<ol>
<li> Open a can of garbonzo beans.
<li> Crush them in a blender.
<li> Add 3 tablesppons of tahini sauce.
<li> Squeeze in one lemon.
<li> Add salt, pepper, and buttercream frosting to taste.
</ol>

</body>
</html>

""", 
   'http://udacity.com/cs101x/urank/arsenic.html': """<html>
<body>
<h1>
The Arsenic Chef's World Famous Hummus Recipe
</h1>
<p>

<ol>
<li> Kidnap the <a href="http://udacity.com/cs101x/urank/nickel.html">Nickel Chef</a>.
<li> Force her to make hummus for you.
</ol>

</body>
</html>

""", 
   'http://udacity.com/cs101x/urank/hummus.html': """<html>
<body>
<h1>
Hummus Recipe
</h1>
<p>

<ol>
<li> Go to the store and buy a container of hummus.
<li> Open it.
</ol>

</body>
</html>




""", 
}

def crawl_web(seed): # returns index, graph of inlinks
    persistent_index=redis.Redis(host="localhost", db=2)
    persistent_graph=redis.Redis(host="localhost", db=3)
    tocrawl = [seed]
    crawled = []
    graph = {}  # <url>, [list of pages it links to]
    index = {} 
    while tocrawl: 
        page = tocrawl.pop()
        if page not in crawled:
            content = get_page(page)
            add_page_to_index(index, page, content)
            outlinks = get_all_links(content)
            print outlinks
            #Here we need to add link one by one, if not all the links will be one string
            for i in outlinks:
                persistent_graph.lpush(page,i)
                
            #graph[page] = outlinks
            
            
            union(tocrawl, outlinks)
            crawled.append(page)
    return index, graph


def get_page(url):
    if url in cache:
        return cache[url]
    else:
        return None
    
def get_next_target(page):
    start_link = page.find('<a href=')
    if start_link == -1: 
        return None, 0
    start_quote = page.find('"', start_link)
    end_quote = page.find('"', start_quote + 1)
    url = page[start_quote + 1:end_quote]
    return url, end_quote

def get_all_links(page):
    links = []
    while True:
        url, endpos = get_next_target(page)
        if url:
            links.append(url)
            page = page[endpos:]
        else:
            break
    return links


def union(a, b):
    for e in b:
        if e not in a:
            a.append(e)

def add_page_to_index(index, url, content):
    persistent_index=redis.Redis(host="localhost", db=2)
    words = content.split()
    for word in words:
        add_to_index(persistent_index, word, url)
        
def add_to_index(persistent_index, keyword, url):
    #modified for using with redis
    
    #if keyword in index:
    #    index[keyword].append(url)
    #else:
    #    index[keyword] = [url]
    persistent_index.lpush(keyword,url)
    
    
def lookup(index, keyword):
    persistent_index=redis.Redis(host="localhost", db=2)
    
    output=persistent_index.lrange(keyword,0,-1)
    return output
    #if keyword in index:
    #    return index[keyword]
    #else:
    #    return None

#we need to create the connections to the database, one conection to index_database and one conecton to graph_database
index = redis.Redis(host="localhost", db=2)#using database number 2 for store index
graph = redis.Redis(host="localhost", db=3)#using database number 3 for store graph
rank = redis.Redis(host="localhost", db=4)#using  database number 4 for store ranks

index, graph = crawl_web('http://udacity.com/cs101x/urank/index.html')
ranks = compute_ranks()
#print lookup(index,'a')
#print ranks
#print index
#1.- Create the connection to the index (in the crawl_web function ) and graph database 
#2.- modify crawl_web (graph) ,  add_page_to_index and add_to_index function
#3.- modify teh lookup function
#4.- Modify crawl_web to make the graph list
#5.- MOdify compute_rank

#>>> {'http://udacity.com/cs101x/urank/kathleen.html': 0.11661866666666663,
#'http://udacity.com/cs101x/urank/zinc.html': 0.038666666666666655,
#'http://udacity.com/cs101x/urank/hummus.html': 0.038666666666666655,
#'http://udacity.com/cs101x/urank/arsenic.html': 0.054133333333333325,
#'http://udacity.com/cs101x/urank/index.html': 0.033333333333333326,
#'http://udacity.com/cs101x/urank/nickel.html': 0.09743999999999997}
