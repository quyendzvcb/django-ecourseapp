from django.contrib.auth import get_permission_codename
from django.db.models.functions import Replace
from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.response import Response
from rest_framework.decorators import action
from courses import serializers, paginators, perms
from courses.models import Category, Course, Lesson, User, Comment, Like


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class CourseViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Course.objects.filter(active=True)
    serializer_class = serializers.CourseSerializer
    pagination_class = paginators.CoursePaginator

    def get_queryset(self):
        query = self.queryset

        if self.action.__eq__('list'):
            q = self.request.query_params.get('q')
            if q:
                query = query.filter(subject__icontains=q)

            cate_id = self.request.query_params.get('category_id')
            if cate_id:
                query = query.filter(category_id=cate_id)

        return query

    @action(methods=['get'], url_path='lessons', detail=True)
    def get_lessons(self, request, pk):
        lessons = self.get_object().lesson_set.filter(active=True)

        q = request.query_params.get('q')
        if q:
            lessons = lessons.filter(subject__icontains=q)

        return Response(serializers.LessonSerializer(lessons, many=True).data, status=status.HTTP_200_OK)


class LessonViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = Lesson.objects.prefetch_related('tags').filter(active=True)
    serializer_class = serializers.LessonDetailsSerializer


    def get_permissions(self):
        if self.action in ['add_comment']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny(), ]

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return serializers.AuthenticatedLessonDetailsSerializer

        return serializers.LessonDetailsSerializer


    @action(methods=['get'], url_path='comments', detail=True)
    def get_comments(self, request, pk):
        # queryset = self.filter_queryset(self.get_queryset())
        #
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        #
        # serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)

        comments = self.get_object().comment_set.select_related('user').order_by('-id')

        paginator = paginators.CommentPaginator()
        page = paginator.paginate_queryset(comments, request)
        if page is not None:
            serializer = serializers.CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        return Response(serializers.CommentSerializer(comments, many=True).data, status=status.HTTP_200_OK)


    @action(methods=['post'], url_path='comments', detail=True)
    def add_comments(self, request, pk):
        c = self.get_object().comment_set.create(content=request.data.get['content'], user=request.user)

        return Response(serializers.CommentSerializer(c).data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], url_path='like', detail=True)
    def like(self, request, pk):
        li, created = Like.objects.get_or_create(user=request.user, lesson=self.get_object())

        if not created:
            li.active =  not li.active
            li.save()

        return Response(serializers.AuthenticatedLessonDetailsSerializer(self.get_object()).data, status=status.HTTP_201_CREATED)



class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser, ]

    def get_permissions(self):
        if self.action in ['get_current_user']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny(), ]

    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        user = request.user
        if request.method.__eq__('PATCH'):
            for k, v in request.data.items():
                setattr(user, k, v)
            user.save()

        return Response(serializers.UserSerializer(user).data)


class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    permission_classes = [perms.CommentOwner]