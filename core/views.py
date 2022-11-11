from http.client import HTTPResponse
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile,Post,LikePost,FollowersCount
from itertools import chain

# Create your views here.

@login_required(login_url='/signin')    #using a decorator
def index(request):
    # return HttpResponse("Hello")
    user_object = User.objects.get(username= request.user.username)
    user_profile= Profile.objects.get(user=user_object)

    user_feed=[]

    user_following = FollowersCount.objects.filter(follower=request.user.username) # all FollowsCount object where follower is user

    for following in user_following: 
        _post= Post.objects.filter(user= following.user) # getting all the post by users of user_following
        user_feed= list(chain(user_feed,_post))
        
    
    # if you want to see your post in your feed, then uncommnet below code
    # Note- feed as of now is not proper according to their time of post.
    # _post = Post.objects.filter(user= request.user.username)
    # user_feed.append(_post)
    
   #user_feed= list(chain(*user_feed)) # chain - It is a function that takes a series of iterables and returns one iterable.
    # for eg = x= [1,2,3], y= [5,6]
    # new_list= list(chain(x,y))
    


    return render(request, 'index.html',{'user_profile':user_profile,'posts':user_feed})


def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']   # we match password== password2

        if password != password2:
            messages.info(request, "Password not matching")
            return redirect('signup')

        elif User.objects.filter(email=email).exists():
            messages.info(request, "Email taken")
            return redirect('signup')

        elif User.objects.filter(username=username).exists():
            messages.info(request, "Username taken")
            return redirect('signup')

        user = User.objects.create_user(  # create_user is a predefined Django function
            username=username, email=email, password=password)
        user.save()

        # Log user in and take to settings page
        # authentication means to check whether a user with given username and password exists in the User model(User model is a Django defined model) or not.
        # If not, it will return None 
        user_login = auth.authenticate(username=username,password=password)  
        auth.login(request,user_login)

        # Create the Profile for the saved user
        user_model = User.objects.get(username=username)
        user_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
        user_profile.save()

        return redirect('/settings')  # whenever there is a signup, it will go to its account settings

    else:
        return render(request, 'signup.html')

def signin(request):


    if request.method=='POST':
        username = request.POST['username']
        password= request.POST['password']

        user = auth.authenticate(username=username,password=password)

        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            messages.info(request,'Invalid Credentials')
            return redirect('/signin')
    
    else:
        return render(request,'signin.html')


@login_required(login_url='/signin')
def logout(request):

    auth.logout(request)
    return redirect('/signin')

@login_required(login_url='/signin')
def settings(request):

    user_profile = Profile.objects.get(user=request.user)

    if request.method=="POST":
        if request.FILES.get('image') != None:
            img = request.FILES.get('image')
        else:
            img = user_profile.profileImg
        bio = request.POST['bio']
        location= request.POST['location']

        user_profile.profileImg =img
        user_profile.bio=bio
        user_profile.location=location
        user_profile.save()
    return render(request,'settings.html',{'user_profile':user_profile})

@login_required(login_url='/signin')
def upload(request):
    if request.method=='POST':
        user = request.user.username
        image = request.FILES.get('upload_image')
        caption= request.POST['caption']
        new_Post = Post.objects.create(user=user,image=image,caption=caption)
        new_Post.save()
        return redirect('/')
    else:    
        return redirect('/')

@login_required(login_url='/signin')
def like_post(request):
    username = request.user.username
    post_id= request.GET.get('post_id')

    post= Post.objects.get(id=post_id)  # get gives only one object(use get over filter when you are sure there is only one object available in the database)

    like_filter = LikePost.objects.filter(post_id=post_id,username=username).first()

    if like_filter ==None:
        new_like= LikePost.objects.create(post_id=post_id,username=username)
        new_like.save()

        post.no_of_likes = post.no_of_likes+1
        post.save()
        return redirect('/')  # redirect to index.html

    else:  # if user clickes again, then unlike the post
        like_filter.delete()

        post.no_of_likes = post.no_of_likes-1
        post.save()
        return redirect('/')  # redirect to index.html


@login_required(login_url='/signin')
def profile(request,pk):

    user_object = User.objects.get(username= pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts= Post.objects.filter(user=pk)
    user_posts_length= len(user_posts)

    is_following= FollowersCount.objects.filter(follower=request.user.username,user=pk).first() # check if our client is already following the user or not
    if is_following!= None: # this means client is following the user
        is_following = True
    else: # client is not following the user
        is_following = False
    
    followerCount_ = FollowersCount.objects.filter(user=pk)
    followerCount_= len(followerCount_)

    followingCount_= FollowersCount.objects.filter(follower=pk)
    followingCount_= len(followingCount_)

    context ={
        'user_object' : user_object,
        'user_profile' : user_profile,
        'user_posts' : user_posts,
        'user_posts_length':user_posts_length,
        'is_following':is_following,
        'followerCount_':followerCount_,
        'followingCount_':followingCount_,

    }
    return render(request,'profile.html',context)

@login_required(login_url='/signin')
def follow(request):
    if request.method=='POST':
        follower = request.POST['follower'] # person that is logged in and will follow the user
        user = request.POST['user'] # person whom follower will follow

        # check if follower is already following the user or not
        check_follower = FollowersCount.objects.filter(follower=follower,user=user).first()

        if check_follower !=None:  #this means follower is already following the user
            check_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = FollowersCount.objects.create(user=user,follower=follower)
            new_follower.save()
            return redirect('/profile/'+user)




